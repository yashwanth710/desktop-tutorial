
# import os
# import logging
# from typing import List, Dict, Any
# import PyPDF2
# import pytesseract
# from pdf2image import convert_from_bytes, convert_from_path
# from PIL import Image, ImageEnhance
# import cv2
# import numpy as np
# import re
# import tempfile
# import io
# import streamlit as st

# logger = logging.getLogger(__name__)

# class PDFProcessor:
#     def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
#         self.chunk_size = chunk_size
#         self.chunk_overlap = chunk_overlap
        
#     def extract_text_from_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
#         """Extract text directly from PDF bytes using PyPDF2"""
#         chunks = []
        
#         try:
#             pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            
#             for page_num in range(len(pdf_reader.pages)):
#                 try:
#                     page = pdf_reader.pages[page_num]
#                     text = page.extract_text()
                    
#                     if text and text.strip():
#                         # Detect visuals in the page
#                         has_visuals = self.detect_visuals_in_page(page)
                        
#                         page_chunks = self.create_chunks(text, page_num + 1, has_visuals)
#                         chunks.extend(page_chunks)
#                         logger.info(f"Page {page_num + 1}: Extracted {len(text)} characters")
#                     else:
#                         logger.warning(f"Page {page_num + 1}: No text found, will try OCR")
#                         # Fall back to OCR
#                         ocr_chunks = self.extract_text_with_ocr(pdf_bytes, page_num + 1)
#                         chunks.extend(ocr_chunks)
                        
#                 except Exception as e:
#                     logger.error(f"Error processing page {page_num + 1}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"PDF extraction error: {e}")
#             st.error(f"PDF extraction error: {e}")
            
#         return chunks
    
#     def detect_visuals_in_page(self, page) -> bool:
#         """Detect if page contains visual elements"""
#         try:
#             # Check for images in PDF (PyPDF2 approach)
#             if '/XObject' in page['/Resources']:
#                 xObject = page['/Resources']['/XObject'].get_object()
#                 for obj in xObject:
#                     if xObject[obj]['/Subtype'] == '/Image':
#                         return True
            
#             # Check for complex formatting that might indicate tables/diagrams
#             text = page.extract_text()
#             if text:
#                 # Look for patterns that might indicate visual content
#                 lines = text.split('\n')
#                 if len(lines) > 50:  # Many short lines might indicate a table
#                     return True
                    
#             return False
            
#         except Exception:
#             return False
    
#     def extract_text_with_ocr(self, pdf_bytes: bytes, page_num: int) -> List[Dict[str, Any]]:
#         """Extract text using OCR for specific page"""
#         chunks = []
        
#         try:
#             # Convert specific page to image
#             images = convert_from_bytes(pdf_bytes, first_page=page_num, last_page=page_num)
            
#             if images:
#                 image = images[0]
#                 text = self.extract_text_from_image(image)
                
#                 # Detect visuals in the image
#                 has_visuals = self.detect_visuals_in_image(image)
                
#                 if text and text.strip():
#                     page_chunks = self.create_chunks(text, page_num, has_visuals)
#                     chunks.extend(page_chunks)
#                     logger.info(f"Page {page_num} (OCR): Extracted {len(text)} characters")
#                 else:
#                     logger.warning(f"Page {page_num}: OCR failed to extract text")
        
#         except Exception as e:
#             logger.error(f"OCR error for page {page_num}: {e}")
#             st.error(f"OCR error for page {page_num}: {e}")
            
#         return chunks
    
#     def detect_visuals_in_image(self, image: Image.Image) -> bool:
#         """Detect visual elements in image using OpenCV"""
#         try:
#             # Convert to OpenCV format
#             cv_image = np.array(image.convert('RGB'))
#             cv_image = cv_image[:, :, ::-1].copy()  # RGB to BGR
            
#             # Edge detection
#             gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
#             edges = cv2.Canny(gray, 50, 150)
            
#             # Count contours
#             contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
#             # If we have many contours, likely a visual element
#             large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]
#             return len(large_contours) > 5
            
#         except Exception as e:
#             logger.error(f"Visual detection error: {e}")
#             return False
    
#     def extract_text_from_image(self, image: Image.Image) -> str:
#         """Extract text from image using OCR"""
#         try:
#             # Preprocess image for better OCR
#             processed_image = self.preprocess_image(image)
            
#             # OCR configuration
#             config = r'--oem 3 --psm 6'
            
#             # Extract text
#             text = pytesseract.image_to_string(processed_image, config=config)
            
#             # Clean up text
#             text = self.clean_text(text)
#             return text
            
#         except Exception as e:
#             logger.error(f"OCR error: {e}")
#             st.error(f"OCR error: {e}")
#             return ""
    
#     def preprocess_image(self, image: Image.Image) -> Image.Image:
#         """Preprocess image for better OCR results"""
#         try:
#             # Convert to grayscale
#             if image.mode != 'L':
#                 image = image.convert('L')
            
#             # Enhance contrast
#             enhancer = ImageEnhance.Contrast(image)
#             image = enhancer.enhance(2.0)
            
#             # Enhance sharpness
#             enhancer = ImageEnhance.Sharpness(image)
#             image = enhancer.enhance(2.0)
            
#             return image
            
#         except Exception as e:
#             logger.error(f"Image preprocessing error: {e}")
#             return image
    
#     def clean_text(self, text: str) -> str:
#         """Clean extracted text"""
#         if not text:
#             return ""
        
#         # Remove excessive whitespace
#         text = re.sub(r'\s+', ' ', text)
        
#         # Remove special characters but keep basic punctuation
#         text = re.sub(r'[^\w\s.,!?\-()\[\]{}:;"\'\/]', '', text)
        
#         # Fix common OCR errors
#         text = re.sub(r'\s+([.,!?])', r'\1', text)  # Remove space before punctuation
#         text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)  # Fix hyphenated words
        
#         return text.strip()
    
#     def create_chunks(self, text: str, page_num: int, has_visuals: bool = False) -> List[Dict[str, Any]]:
#         """Split text into chunks with metadata"""
#         if not text.strip():
#             return []
        
#         chunks = []
#         words = text.split()
#         current_chunk = []
#         current_length = 0
        
#         for i, word in enumerate(words):
#             word_length = len(word) + 1  # +1 for space
            
#             if current_length + word_length > self.chunk_size and current_chunk:
#                 # Create chunk
#                 chunk_text = ' '.join(current_chunk)
#                 chunk_data = {
#                     'text': chunk_text,
#                     'page_number': page_num,
#                     'chunk_id': f"page_{page_num}_chunk_{len(chunks) + 1}",
#                     'has_visuals': has_visuals
#                 }
#                 chunks.append(chunk_data)
                
#                 # Keep overlap for next chunk
#                 overlap_words = min(len(current_chunk), max(1, self.chunk_overlap // 10))
#                 current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
#                 current_length = sum(len(w) + 1 for w in current_chunk)
            
#             current_chunk.append(word)
#             current_length += word_length
        
#         # Add final chunk
#         if current_chunk:
#             chunk_text = ' '.join(current_chunk)
#             chunk_data = {
#                 'text': chunk_text,
#                 'page_number': page_num,
#                 'chunk_id': f"page_{page_num}_chunk_{len(chunks) + 1}",
#                 'has_visuals': has_visuals
#             }
#             chunks.append(chunk_data)
        
#         return chunks
    
#     def process_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
#         """Process entire PDF from bytes and return chunks"""
#         logger.info("Processing PDF from bytes")
        
#         # First try direct text extraction
#         chunks = self.extract_text_from_pdf(pdf_bytes)
        
#         # If no text was extracted, try OCR for the whole document
#         if not chunks:
#             logger.info("No text found with direct extraction, trying full OCR...")
#             st.warning("No text found with direct extraction, trying OCR...")
#             chunks = self.process_pdf_with_ocr(pdf_bytes)
        
#         logger.info(f"Processing complete. Created {len(chunks)} chunks")
#         return chunks
    
#     def process_pdf_with_ocr(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
#         """Process PDF using OCR for all pages"""
#         chunks = []
        
#         try:
#             # Convert PDF to images
#             images = convert_from_bytes(pdf_bytes)
            
#             for page_num, image in enumerate(images, 1):
#                 try:
#                     # Extract text using OCR
#                     text = self.extract_text_from_image(image)
                    
#                     # Detect visuals
#                     has_visuals = self.detect_visuals_in_image(image)
                    
#                     if text and text.strip():
#                         page_chunks = self.create_chunks(text, page_num, has_visuals)
#                         chunks.extend(page_chunks)
#                         logger.info(f"Page {page_num} (OCR): Extracted {len(text)} characters")
#                     else:
#                         logger.warning(f"Page {page_num}: OCR failed to extract text")
                        
#                 except Exception as e:
#                     logger.error(f"Error processing page {page_num}: {e}")
#                     continue
                    
#         except Exception as e:
#             logger.error(f"PDF to image conversion error: {e}")
#             st.error(f"PDF conversion error: {e}. Please install poppler-utils.")
            
#         return chunks

import os
import logging
from typing import List, Dict, Any
import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image, ImageEnhance
import cv2
import numpy as np
import re
import tempfile
import io
import streamlit as st
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import time

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, max_workers: int = 4):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Process entire PDF from bytes and return chunks asynchronously"""
        logger.info("Processing PDF from bytes asynchronously")
        
        # First try direct text extraction
        chunks = await self.extract_text_from_pdf_async(pdf_bytes)
        
        # If no text was extracted, try OCR for the whole document
        if not chunks:
            logger.info("No text found with direct extraction, trying full OCR...")
            st.warning("No text found with direct extraction, trying OCR...")
            chunks = await self.process_pdf_with_ocr_async(pdf_bytes)
        
        logger.info(f"Processing complete. Created {len(chunks)} chunks")
        return chunks
    
    async def extract_text_from_pdf_async(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract text directly from PDF bytes using PyPDF2 asynchronously"""
        chunks = []
        
        try:
            # Run PDF reading in thread pool
            pdf_reader = await asyncio.get_event_loop().run_in_executor(
                self.executor, PyPDF2.PdfReader, io.BytesIO(pdf_bytes)
            )
            
            # Process pages concurrently
            page_tasks = []
            for page_num in range(len(pdf_reader.pages)):
                task = self.process_page_async(pdf_reader.pages[page_num], page_num + 1)
                page_tasks.append(task)
            
            # Gather results from all pages
            page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
            
            for result in page_results:
                if isinstance(result, Exception):
                    logger.error(f"Page processing error: {result}")
                    continue
                if result:
                    chunks.extend(result)
                    
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            st.error(f"PDF extraction error: {e}")
            
        return chunks
    
    async def process_page_async(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Process a single page asynchronously"""
        try:
            # Extract text in thread pool
            text = await asyncio.get_event_loop().run_in_executor(
                self.executor, page.extract_text
            )
            
            if text and text.strip():
                # Detect visuals in the page
                has_visuals = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.detect_visuals_in_page, page
                )
                
                # Create chunks
                page_chunks = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.create_chunks, text, page_num, has_visuals
                )
                
                logger.info(f"Page {page_num}: Extracted {len(text)} characters")
                return page_chunks
            else:
                logger.warning(f"Page {page_num}: No text found")
                return []
                
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}")
            return []
    
    async def process_pdf_with_ocr_async(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Process PDF using OCR for all pages asynchronously"""
        chunks = []
        
        try:
            # Convert PDF to images in thread pool
            images = await asyncio.get_event_loop().run_in_executor(
                self.executor, convert_from_bytes, pdf_bytes
            )
            
            # Process images concurrently
            image_tasks = []
            for page_num, image in enumerate(images, 1):
                task = self.process_image_with_ocr_async(image, page_num)
                image_tasks.append(task)
            
            # Gather results from all images
            image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
            
            for result in image_results:
                if isinstance(result, Exception):
                    logger.error(f"Image processing error: {result}")
                    continue
                if result:
                    chunks.extend(result)
                    
        except Exception as e:
            logger.error(f"PDF to image conversion error: {e}")
            st.error(f"PDF conversion error: {e}. Please install poppler-utils.")
            
        return chunks
    
    async def process_image_with_ocr_async(self, image: Image.Image, page_num: int) -> List[Dict[str, Any]]:
        """Process a single image with OCR asynchronously"""
        try:
            # Extract text using OCR in thread pool
            text = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.extract_text_from_image, image
            )
            
            # Detect visuals in thread pool
            has_visuals = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.detect_visuals_in_image, image
            )
            
            if text and text.strip():
                # Create chunks in thread pool
                page_chunks = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.create_chunks, text, page_num, has_visuals
                )
                
                logger.info(f"Page {page_num} (OCR): Extracted {len(text)} characters")
                return page_chunks
            else:
                logger.warning(f"Page {page_num}: OCR failed to extract text")
                return []
                
        except Exception as e:
            logger.error(f"Error processing image {page_num}: {e}")
            return []
    
    def detect_visuals_in_page(self, page) -> bool:
        """Detect if page contains visual elements"""
        try:
            # Check for images in PDF (PyPDF2 approach)
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        return True
            
            # Check for complex formatting that might indicate tables/diagrams
            text = page.extract_text()
            if text:
                # Look for patterns that might indicate visual content
                lines = text.split('\n')
                if len(lines) > 50:  # Many short lines might indicate a table
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def detect_visuals_in_image(self, image: Image.Image) -> bool:
        """Detect visual elements in image using OpenCV"""
        try:
            # Convert to OpenCV format
            cv_image = np.array(image.convert('RGB'))
            cv_image = cv_image[:, :, ::-1].copy()  # RGB to BGR
            
            # Edge detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Count contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # If we have many contours, likely a visual element
            large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]
            return len(large_contours) > 5
            
        except Exception as e:
            logger.error(f"Visual detection error: {e}")
            return False
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        try:
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image)
            
            # OCR configuration
            config = r'--oem 3 --psm 6'
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=config)
            
            # Clean up text
            text = self.clean_text(text)
            return text
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            st.error(f"OCR error: {e}")
            return ""
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            return image
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return image
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?\-()\[\]{}:;"\'\/]', '', text)
        
        # Fix common OCR errors
        text = re.sub(r'\s+([.,!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub (r'(\w)-\s+(\w)', r'\1\2', text)  # Fix hyphenated words
        
        return text.strip()
    
    def create_chunks(self, text: str, page_num: int, has_visuals: bool = False) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        if not text.strip():
            return []
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for i, word in enumerate(words):
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk_data = {
                    'text': chunk_text,
                    'page_number': page_num,
                    'chunk_id': f"page_{page_num}_chunk_{len(chunks) + 1}",
                    'has_visuals': has_visuals
                }
                chunks.append(chunk_data)
                
                # Keep overlap for next chunk
                overlap_words = min(len(current_chunk), max(1, self.chunk_overlap // 10))
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
            
            current_chunk.append(word)
            current_length += word_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_data = {
                'text': chunk_text,
                'page_number': page_num,
                'chunk_id': f"page_{page_num}_chunk_{len(chunks) + 1}",
                'has_visuals': has_visuals
            }
            chunks.append(chunk_data)
        
        return chunks
    
    async def close(self):
        """Clean up resources"""
        self.executor.shutdown(wait=True)