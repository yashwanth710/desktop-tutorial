import pymupdf
import base64
import os
from typing import List, Any, Dict
import asyncio

from schemas.models import FullPageData
from models.openai import VisionModelWrapper


class ImageExtractor():

    def __init__(self):
        self.vision_model = VisionModelWrapper()

    async def extract_full_page_content(self, page,dpi:int, source:str):
        """Extract every content from the given pdf page including text, figures, images and tables."""

        try:
            pix = page.get_pixmap(dpi = dpi)
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
           
            result = await self.vision_model.run(img_base64)
            print(f"Extraction is in Progress for page number {page.number}")
            print(result.strip())
            file_name = os.path.basename(source)
            proposal_number = file_name.split("_")[0].strip() 
            metadata = {"page" : page.number,
                        "source" : source,
                        "type": "full",
                        "proposal_number" : proposal_number
                        }
            return FullPageData(content = result.strip(),
                                metadata=metadata)
            
        except Exception as e:
            error_msg = str(e)
            if "The image is too large" in error_msg:
                print("Maximum image size is 20MB for openai. so reducing dpi by 30%")
                new_dpi = int(dpi * 0.7)
                print("new dpi value is ",new_dpi)
                return await self.extract_full_page_content(page,dpi = new_dpi, source=source)

            else:
                print(f"Following Error occured in ImageExtractor: {e}")
                raise 

class PDFParser():
    def __init__(self):
        self.image_extractor = ImageExtractor()
        self.semaphore = None


    async def process_each_page(self,pdf_page, source):

        try:
            async with self.semaphore:
                dpi = 720
                full_page_content = await self.image_extractor.extract_full_page_content(pdf_page, dpi = dpi, source=source)
                #returning tables and images empty lists so that next stage of pipeline don't break.
                return {
                    "text": full_page_content,
                    "tables": [],
                    "images": []
                }
        except Exception as page_error:
            print(f"Error in Processing PDF Page {pdf_page.number}: {page_error}")
            raise 
            
    
        

    async def extract_content(self,pdf_path:str, source) -> List[Dict[str, Any]]:
        """Extract content from given pdf including text, tables and images."""
        print(f"DATA extraction is in progress for pdf {pdf_path}")
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"The specified path does not exist or is not a file: {pdf_path}")
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError(f"The specified file is not a PDF: {pdf_path}")
        
        self.semaphore = asyncio.Semaphore(30)
        documents = []
        try:
            with pymupdf.open(pdf_path) as pdf_document:
                page_tasks = []

                for page_num in range(pdf_document.page_count):
                    page_tasks.append(self.process_each_page(pdf_document[page_num], source))

                page_results = await asyncio.gather(*page_tasks, return_exceptions= True)

                for page_result in page_results:
                    if isinstance(page_result, Exception):
                        raise page_result
                    else:
                        documents.append(page_result)

                return documents

        except Exception as e:
            print(f"issue with extracting pdf content: {e}")
            raise 
