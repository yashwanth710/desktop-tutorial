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
import requests
from doctr.models import ocr_predictor
from datetime import datetime
from doctr.io import DocumentFile
from openai import OpenAI

def extract_text_from_pdf(pdf_path):
    model = ocr_predictor(pretrained=True)
    doc = DocumentFile.from_pdf(pdf_path)
    result = model(doc)
    
    def sort_by_coordinates(element):
        return (element.geometry[0][1], element.geometry[0][0]) 

    page_text = {} 
    for num, page in enumerate(result.pages):
        text = ""
        line_list = []

        for block in page.blocks:
            line_list.extend(block.lines)

        sorted_lines = sorted(line_list, key=sort_by_coordinates)

        for line in sorted_lines:
            for word in line.words:
                text += word.value + " "
            text += "\n"
        
        page_text[num] = text + "\n"

    return page_text



# Initialize OpenAI client
client = OpenAI(api_key='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')

def is_relevant(text, prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"'{prompt}':\n\n context: {text}\n\nAnswer with 'Yes' or 'No'."}
        ]
    )
    return response.choices[0].message.content.strip().lower() == 'yes'

def find_relevant_pages(pdf_path, prompt):
    text_by_page = extract_text_from_pdf(pdf_path)
    relevant_pages = []

    for page_number, text in text_by_page.items():
        if is_relevant(text, prompt):
            relevant_pages.append(page_number)

    return relevant_pages




def table_extraction(pdf_path, relevant_pages):
    pdf_document = fitz.open(pdf_path)
    pdf = PDF(src=pdf_path, pages= relevant_pages)
    ocr = TesseractOCR(lang="eng")
    pdf_tables = pdf.extract_tables(ocr=ocr)
    tables = []
    for page in relevant_pages:
        for table in pdf_tables[page]:
            tables.append(table.df)  
    return tables
