
# pdf readers
# relevant pages
# data extraction

import json 
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import os 
import pandas as pd
import re
import json
from img2table.document import PDF
from img2table.ocr import TesseractOCR


#################### Image Extraction #######################

# def extract_images_from_pdf(page, pdf_document):
#     images = []
#     image_list = page.get_images(full=True)
#     for img_index, img in enumerate(image_list):
#         xref = img[0]
#         base_image = pdf_document.extract_image(xref)
#         image_bytes = base_image["image"]
#         image = Image.open(io.BytesIO(image_bytes))
#         images.append(image)
#     return images

# # Main function
# def image_data(pdf_document, page):
#     images = extract_images_from_pdf(page, pdf_document)
#     image_info=''
#     for image in images:
#         table_data = pytesseract.image_to_string(image, config='--psm 4')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
#         image_info += table_data

#     #### take to string instead of list directly
#     return image_info   



################################ Text by Page #######################################

# def extract_text_from_pdf(pdf_path):
#     pdf_document = fitz.open(pdf_path)
#     text_by_page = {}
    

#     image_text = '' ###For temporary use only 
 
#     for page_number in range(len(pdf_document)):
#         page = pdf_document.load_page(page_number)
#         page_txt=""
#         text = page.get_text()
#### IMAGE_TEXT is commented for testing purposes.
######         image_text=image_data(pdf_document, page)
        
        # for m in range(len(image_text)):
        #     img_txt += image_text[m] 
    #     page_txt =f"{text} + IMAGE DATA____ {image_text}"
    #     text_by_page[page_number] = page_txt  

    # return text_by_page
    
    
    
######################  Text by Page############################

def extract_text_from_pdf(pdf_path):
    
    # Open PDF Document
    pdf_document = fitz.open(pdf_path)
    text_by_page = {}
    
    # Iterate through each page in the PDF
    for page_number in range(len(pdf_document)):
        # Load the page and extract its text
        page = pdf_document.load_page(page_number)
        text = page.get_text()
        text_by_page[page_number] = text  

    return text_by_page



########################## Table Extraction ########################
 

def table_extraction(pdf_path, relevant_pages):
    pdf_document = fitz.open(pdf_path)
    pdf = PDF(src=pdf_path, pages= relevant_pages)
    ocr = TesseractOCR(lang="eng")
    pdf_tables = pdf.extract_tables(ocr=ocr)
    tables = []
    for page_number in relevant_pages:
        for table in pdf_tables[page_number]:
            tables.append(table.df)
        return tables
            

