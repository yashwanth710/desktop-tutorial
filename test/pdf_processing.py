
# pdf readers
# relevant pages
# data extraction
# from doctr.models import detection_predictor, recognition_predictor
# from doctr.models import ocr_predictor
# from doctr.io import DocumentFile
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from prompts import relevant_page_level_dictionary
import os, json, re
import pandas as pd 
from openai import OpenAI
import numpy as np 

from prompts import *
# import torch
# import tensorflow as tf
# # Resetting the default graph in TensorFlow 2.x
# tf.compat.v1.reset_default_graph()

from onnxtr.io import DocumentFile
from onnxtr.models import ocr_predictor


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
    # recognition_model = recognition_predictor(arch='crnn_vgg16_bn', pretrained=False)
    # # reco_params = torch.load(f"{path}\PDF_Scraper\models\crnn_vgg16_bn_weights.pth", map_location="cpu", weights_only= True)
    # reco_params = torch.load("/app/models/crnn_vgg16_bn_weights.pth", map_location="cpu", weights_only= True)

    # recognition_model.load_state_dict(reco_params)

    # detection_model = detection_predictor(arch='db_resnet50', pretrained=False)
    # # detec_model = torch.load(f"{path}\PDF_Scraper\models\db_resnet50_weights.pth", map_location="cpu", weights_only= True)
    # detec_model = torch.load("/app/models/db_resnet50_weights.pth", map_location="cpu", weights_only= True)
    # detection_model.load_state_dict(detec_model)

    # model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=False, straighten_pages= True)
    # model.det_predictor.model = detection_model.model
    # model.reco_predictor.model = recognition_model.model
    model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', det_bs=2, reco_bs=512, assume_straight_pages=True, straighten_pages=False, detect_orientation=False)
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
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You function as a bot specializing in recognizing information from oil analysis reports in the electrical sector."},
            {"role": "user", "content": f"'{prompt}':\n\n context: {text}\n\nAnswer with 'Yes' or 'No'."}])
#     print(text)
    return response.choices[0].message.content.strip().lower() == 'yes'

########################## Finding Relevant Pages #########################

def find_relevant_pages(input_json, text_by_page):

    selected_tests = [i["test_type"] for i in input_json['selectedTests']]
    print(selected_tests)
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
    print('Extracting text from PDF...')
    text_by_page = extract_text_from_pdf(pdf_path)
    print('finding relevant pages for requested test...')
    relevant_pages_dict = find_relevant_pages(input_json, text_by_page)
    print('Extracting Tables from PDF...')
    table_data = table_extraction(pdf_path, relevant_pages_dict)
    relevant_data= rel_data(text_by_page, relevant_pages_dict, table_data)
    return relevant_data


########################### Convert and Evaluate ###########################

def convert_and_evaluate(expression):

    try:        
        # Replace the multiplication symbol ' x ' or 'X' with '*'
        expression = expression.replace(' x ', ' * ').replace('X', '*')

        # Replace '^' with '**' for exponentiation
        expression = expression.replace('^', '**')
        
        # Replace '10' followed by digits with '10**' followed by those digits
        expression = re.sub(r'10(\d+)', r'10**\1', expression)
        
        # Replace superscript numbers with regular numbers
        superscript_map = {
            '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
            '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
        }
        expression = re.sub(r'[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+', lambda x: ''.join(superscript_map.get(char, char) for char in x.group()), expression)
        expression = re.sub(r'(\d+)\*\*(\d+)', r'\1**\2', expression)  # Handle remaining superscript conversions
        
        # Evaluate the expression
        result = eval(expression)
        
        return result
    except Exception:
        return expression

############################# DGA Template creation ##########################

def DGA_template_creation(response, combined_json ,meta_data_json):
    response = response[8:-4:]
    response = response.replace('\n', '')
    response = json.loads(response)

    # Table Creation 
    
    transformed_data = []
    for display_name, values in response.items():
        new_entry = {'DISPLAYNAME': display_name}
        tag_name = combined_json.get(display_name, "")
        new_entry['TAGNAME'] = tag_name
        new_entry.update(values)
        transformed_data.append(new_entry)
    table_oil = pd.DataFrame(transformed_data)
        
    #final_data['POSITION'].bfill(inplace = True)
    #final_data = final_data.iloc[:-1]
    print('NEEEEEEEEEEEEEEEEEEEEEEEEXXXXXXXXXTTTTTTTTTTTTTTTTT')
#    table_oil = pd.merge(temp_df, final_data, on=['DISPLAYNAME'], how='left')
    contains_ohm = table_oil['LIMITS'].str.contains('Ω-cm').fillna(False)
    contains_gohm = table_oil['LIMITS'].str.contains('GΩm').fillna(False)
    #if contains_ohm.any() or contains_gohm.any() == True:
    try:
        oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 27°C")
        if oil_resistivity_mask.any():
            expression = table_oil.loc[oil_resistivity_mask, "VALUETEXT"][table_oil.loc[oil_resistivity_mask, "VALUETEXT"].index[0]]
            table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = convert_and_evaluate(expression)                    

        oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 90°C")
        if oil_resistivity_mask.any():
            expression = table_oil.loc[oil_resistivity_mask, "VALUETEXT"][table_oil.loc[oil_resistivity_mask, "VALUETEXT"].index[0]]
            table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = convert_and_evaluate(expression)
            
    except ValueError:
        pass
        
    try:
        table_oil.loc[contains_ohm, "VALUETEXT"] = pd.to_numeric(table_oil.loc[contains_ohm, "VALUETEXT"], errors="coerce")
        table_oil.loc[contains_gohm, "VALUETEXT"] = pd.to_numeric(table_oil.loc[contains_gohm, "VALUETEXT"], errors="coerce")
        table_oil.loc[contains_ohm, 'VALUETEXT'] *= 10**12
        table_oil.loc[contains_gohm, 'VALUETEXT'] *= 10**11
    except ValueError:
        pass

    table_oil.drop('LIMITS', axis = 1, inplace = True)
    table_oil['VALUETEXT'] = table_oil['VALUETEXT'].replace({'NIL': np.nan, 'BDL': np.nan, 'N/d' : np.nan, 'N/D' : np.nan,
                                                             'Nil' : np.nan, 'ND' : np.nan, 'Not Detected': np.nan})
    table_oil['VALUETEXT'] = table_oil['VALUETEXT'].fillna('')
    contains_Oil_Appearance	 = table_oil['DISPLAYNAME'].str.contains('Oil Appearance')
    table_oil.loc[contains_Oil_Appearance, 'VALUETEXT'] = table_oil['VALUETEXT'].str.replace('\n',' ')
    # table_oil['DISPLAYNAME'].replace(meta_data_json, inplace=True)
    oil_dict = table_oil.to_dict('records')
    print("Formatting Data........")


    formatted_data = []

    for entry in oil_dict:
        # Extract display name as the key
        display_name = entry.pop('DISPLAYNAME')
        # Structure the desired dictionary for each display name
        formatted_data.append({
            'param_name': entry.get('TAGNAME', ''),
            'test_method': entry.get('TESTMETHOD', ''),
            'value_text': entry.get('VALUETEXT', '')
        })

    meta_data=[]
    normal_data=[]  
    for i in formatted_data:
        if i['param_name'] in meta_data_json.values():
            meta_data.append(i)
        else:
            normal_data.append(i)            
    for entry in meta_data:
        entry['paramname'] = entry.pop('param_name')     

       

    # final_data=normal_data.extend(meta_data)
    return meta_data,normal_data




########### JSON CREATION ############


def tag_check(combined_json):    
    llm_oil_json = {}    
    for key, value in combined_json.items():
        llm_oil_json[key] = {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""}
    return llm_oil_json

# with open("/app/data/name_template.json", "r", encoding='utf-8') as file:
#     json_data = json.load(file)


# with open(f"{path}/PDF_Scraper/data/name_template.json", "r", encoding='utf-8') as file:
#     json_data = json.load(file)
###########



