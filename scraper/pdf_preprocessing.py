
# pdf readers
# relevant pages
# data extraction
from doctr.models import detection_predictor, recognition_predictor
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from prompts import relevant_page_level_dictionary
import os
from openai import OpenAI
import torch
# import tensorflow as tf
# # Resetting the default graph in TensorFlow 2.x
# tf.compat.v1.reset_default_graph()

"""
1. Extract_text_from_pdf(pdf_path)
input_params: pdf_file
using db_resnet50,vgg16_models from doctr to extract text from pdf.
response: page_level_text, format : dictionary
Extract_text_from_pdf(pdf_file)
"""

"""
2.Extract_table_from_pdf(pdf_path,relevant_pages)
input_params: pdf_path,relevant_pages
relevant_pages should be of type list.
response: table_data , format : dictionary
{
    "Oil Testing": text,
    "Winding Resistance": text,
    "Turns Ratio Test": text, 
    "insulation_test": text
    }
"""

"""
3.Finding_relevant_data(input_json,pdf_path)
input_params: input_json
##########################################
test_by_page: Extract_text_from_pdf(pdf_path)
prompts: relevant_pages_prompts() from prompts.py
intital_response: relevant_pages, format : dictionary
{
    "Oil Testing": [14,15],
    "Winding Resistance": [16],
    "Turns Ratio Test": [8],
    "insulation_test":[10]
    }
    
table_data = Extract_table_from_pdf(pdf_path,relevant_pages,test_by_page)

final_response: relevant_data, format : dictionary
{
    "Oil Testing": "text",
    "Winding Resistance": "text",
    "Turns Ratio Test": "text",
    "insulation_test":"text"
    } 

"""
api_key=os.getenv("OPENAI_API_KEY")

# pdf_path = r"C:\Users\Admin\Documents\Offline data reports\MPS\Format - 1\2018 - 001.pdf"
# input_json = { 
# "asset_name": "TR-01", 
# "vendor_name": "mps", 
# "sample_date": "10:11:2020 12:12:12 GMT", 
# "test_date": "10:11:2020 12:12:12 GMT", 
# "Report_type": "Routine", 
# "path": "xyz.pdf",
# "selectedTests": { 
# "Oil Testing": True, 
# "Winding Resistance": False, 
# "Turns Ratio Test": False, 
# "insulation_test": False
# } 
# }
path=os.getcwd()

################################ Text by Page #######################################

def extract_text_from_pdf(pdf_path):

    recognition_model = recognition_predictor(arch='crnn_vgg16_bn', pretrained=False)
    reco_params = torch.load(f"{path}\PDF_Scraper\crnn_vgg16_bn_weights.pth", map_location="cpu")
    recognition_model.load_state_dict(reco_params)

    detection_model = detection_predictor(arch='db_resnet50', pretrained=False)
    detec_model = torch.load(f"{path}\PDF_Scraper\db_resnet50_weights.pth", map_location="cpu")
    detection_model.load_state_dict(detec_model)

    model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=False, straighten_pages= True)
    model.det_predictor.model = detection_model.model
    model.reco_predictor.model = recognition_model.model
    doc = DocumentFile.from_pdf(pdf_path)
    result = model(doc)
    
    def sort_by_coordinates(element):
        return (element.geometry[0][1], element.geometry[0][0]) 
    page_level_text={} 
    for num,page in enumerate(result.pages):
        text = ""
        line_list = []
        
        for block in page.blocks:
            line_list.extend(block.lines)
            
        sorted_lines = sorted(line_list, key=sort_by_coordinates)
        
        for line in sorted_lines:
            for word in line.words:
                text += word.value + " "
            text += "\n"
        page_level_text[num]= text + "\n"
        text += "\n"
    return page_level_text
# print(extract_text_from_pdf(pdf_path)[0])

#############################################################
def is_relevant(text, prompt):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You function as a bot specializing in recognizing information from oil analysis reports in the electrical sector."},
            {"role": "user", "content": f"'{prompt}':\n\n context: {text}\n\nAnswer with 'Yes' or 'No'."}])
#     print(text)
    return response.choices[0].message.content.strip().lower() == 'yes'

########################## Finding Relevant Pages #########################

def find_relevant_pages(input_json, text_by_page):

    selected_tests = [key for key,value in input_json['selectedTests'].items() if value]
    relevant_pages_dict = {}

    # If there are fewer than 5 pages, include all pages as relevant pages
    if len(text_by_page.keys()) < 5:
        all_pages = list(text_by_page.keys())
        for test in selected_tests:
            relevant_pages_dict[test] = all_pages
    else:
        for test in selected_tests:
            relevant_pages = []
            prompt = relevant_page_level_dictionary[test]
            # Iterate through pages and determine relevance
            for _ in range(3):
                for page_number, text in text_by_page.items():
                    if is_relevant(text, prompt):
                        relevant_pages.append(page_number)
            relevant_pages_dict[test] = list(set(relevant_pages))     
    return relevant_pages_dict


# ########################## Table Extraction ########################
def table_extraction(pdf_path, relevant_pages_dict):
    table_data = {}
    for test in relevant_pages_dict:
        if not relevant_pages_dict[test]:
            table_data[test] = ""
        else:    
            # relevant_pages = relevant_pages_dict[test]
            pdf = PDF(src=pdf_path, pages= relevant_pages_dict[test])
            ocr = TesseractOCR(lang="eng")
            pdf_tables = pdf.extract_tables(ocr=ocr)
            # print(pdf_tables)
            tables = []
            str_tables = ""  + "\n"
            for page in relevant_pages_dict[test]:
                for table in pdf_tables[page]:
                    # print(table.df)
                    tables.append(table.df)  
                    # str_tables+= str(table.df)
            table_data[test] = str(tables)       
    return table_data

# ########################## Relevant Data merge ###########################
def rel_data(text_by_page, relevant_pages_dict, table_data):
    relevant_data = {}
    for test, relevant_pages in relevant_pages_dict.items():
        req_relevant_data = [text_by_page[key] for key in relevant_pages]
        table_relevant_data = table_data[test]
        if not req_relevant_data and table_relevant_data:
            relevant_data[test]=""
        else:
            relevant_data[test] = table_relevant_data + str(req_relevant_data)
    return relevant_data


# ############################ Finding Relevant Data ##############################

def finding_relevant_data(input_json, pdf_path):
    text_by_page = extract_text_from_pdf(pdf_path)
    relevant_pages_dict = find_relevant_pages(input_json, text_by_page)
    table_data = table_extraction(pdf_path, relevant_pages_dict)
    relevant_data= rel_data(text_by_page, relevant_pages_dict, table_data)
    return relevant_data



# print(finding_relevant_data(input_json, pdf_path))