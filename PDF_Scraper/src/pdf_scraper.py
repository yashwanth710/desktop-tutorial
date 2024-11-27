# llm functionality
# Json creation(template)

import numpy as np 
import pandas as pd 
import os, json, re
from openai import OpenAI
from datetime import datetime
from onnxtr.io import DocumentFile
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from onnxtr.models import ocr_predictor
from langchain_openai import ChatOpenAI
from prompts import llm_model_prompt_func, relevant_page_level_dictionary
pd.set_option("display.max_columns",100)
"""
1.Extract_test_result_json(input_json,pdf_path)
final_data_json: Finding_relevant_data(input_json,pdf_path)
#####################################################
prompts: llm_model_prompts() from prompts.py
reponse: Output_json:  {
    "Oil Testing": {},
    "Winding Resistance": {},
    "Turns Ratio Test": {},
    "insulation_test":{}
    }
}
"""

"""
2.Test_level_json_creation(input_json,Output_json):

response: Output_json: {
  "asset_name": "TR-01",
  "vendor_name": "mps",
  "sample_date": "10:11:2020 12:12:12 GMT",
  "test_date": "10:11:2020 12:12:12 GMT",
  "Report_type":"Routine",
    "selectedTests": {
    "Oil Testing": {

    },
    "Winding Resistance": {},
    "Turns Ratio Test": {},
    "insulation_test":{}
    }
}

"""
path=os.getcwd()
api_key=os.getenv("OPENAI_API_KEY")

############################################### LLM FUNCTIONALITY (CLASS) ###############################################

class LLM_functionalities:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def is_relevant(self, text, prompt):
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You function as a bot specializing in recognizing information from oil analysis reports in the electrical sector."},
                {"role": "user", "content": f"'{prompt}':\n\n context: {text}\n\nAnswer with 'Yes' or 'No'."}])
    #     print(text)
        return response.choices[0].message.content.strip().lower() == 'yes'

    def model_data(self, data, prompt):    
        # Initialize the OpenAI GPT-4 model for chat
        chat_llm = ChatOpenAI(model="gpt-4o", api_key=self.api_key)
        # Combine the query and document content
        combined_query = prompt + "\n\nDocument Content:\n" + data
        start_time = datetime.now()
    
        # Generate a completion
        response = chat_llm.predict(text=combined_query) # Use predict() instead of chat() for ChatOpenAI
        # end_time = datetime.now()
    #     print('Duration: {}'.format(end_time - start_time))
        
        return response

############################################### Pdf Process Functionality ###############################################

class Pdf_Process:
    def __init__(self, pdf_path, input_json, api_key, relevant_page_level_dictionary):
        self.pdf_path = pdf_path
        self.input_json = input_json        
        self.LLM_functionalities = LLM_functionalities(api_key)
        self.relevant_page_level_dictionary = relevant_page_level_dictionary

        
######################### Text by Page #########################
    
    def extract_text_from_pdf(self):
        model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', det_bs=2, reco_bs=512, assume_straight_pages=True, straighten_pages=False, detect_orientation=False)
        doc = DocumentFile.from_pdf(self.pdf_path)
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
        
######################### Finding Relevant Pages #########################
    
    def find_relevant_pages(self, text_by_page):
        selected_tests = [i["test_type"] for i in self.input_json['selectedTests']]
        relevant_pages_dict = {}
    
        # If there are fewer than 5 pages, include all pages as relevant pages
        if len(text_by_page.keys()) < 5:
            all_pages = list(text_by_page.keys())
            for test in selected_tests:
                relevant_pages_dict[test] = all_pages
        else:
            for test in selected_tests:
                relevant_pages = []
                prompt = self.relevant_page_level_dictionary[test]
                # Iterate through pages and determine relevance
                for _ in range(3):
                    for page_number, text in text_by_page.items():
                        if self.LLM_functionalities.is_relevant(text, prompt):
                            relevant_pages.append(page_number)
                relevant_pages_dict[test] = list(set(relevant_pages))  
        return relevant_pages_dict     
        
######################### Table Extraction #########################
    
    def table_extraction(self, relevant_pages_dict):
        table_data = {}
        for test in relevant_pages_dict:
            if not relevant_pages_dict[test]:
                table_data[test] = ""
            else:    
                # relevant_pages = relevant_pages_dict[test]
                pdf = PDF(src=self.pdf_path, pages= relevant_pages_dict[test])
                ocr = TesseractOCR(lang="eng")
                pdf_tables = pdf.extract_tables(ocr=ocr)
                # print(pdf_tables)
                tables = []
                str_tables = ""  + "\n"
                for page in relevant_pages_dict[test]:
                    for table_no, table in enumerate(pdf_tables[page]):
                        # print(table.df)
                        tables.append(f'Table from page {page}, table number {table_no}:------------------- {table.df}')  
                        # str_tables+= str(table.df)
                table_data[test] = str(tables)       
        return table_data

######################### Relevant Data Merger (TABLE + TEXT) #########################

    def rel_data_merger(self, text_by_page, relevant_pages_dict, table_data):
        relevant_data = {}
        for test, relevant_pages in relevant_pages_dict.items():
            req_relevant_data = [f'Text for page number {page}: -------------------{text_by_page[page]}' for page in relevant_pages]
            table_relevant_data = table_data[test]
            if not req_relevant_data and table_relevant_data:
                relevant_data[test]=""
            else:
                relevant_data[test] = table_relevant_data + str(req_relevant_data)
        return relevant_data

######################### Finding Relevant Data (MIX OF TOP 4 FUNCTIONS) #########################

    def finding_relevant_data(self):
        print('Extracting text from PDF...')
        text_by_page = self.extract_text_from_pdf()
        print('finding relevant pages for requested test...')
        relevant_pages_dict = self.find_relevant_pages(text_by_page)
        print('Extracting Tables from PDF...')
        table_data = self.table_extraction(relevant_pages_dict)
        print('Merging text and table data')
        relevant_data = self.rel_data_merger(text_by_page, relevant_pages_dict, table_data)
        return relevant_data

######################### GPT4o Json Creation(OIL TESTING) #########################
    
    def tag_check(self, combined_json):    
        llm_oil_json = {}    
        for key, value in combined_json.items():
            llm_oil_json[key] = {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""}
        return llm_oil_json


############################################### TEMPLATES CLASS (STATIC) ###############################################

class template_creation:
    
    @staticmethod
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
                table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = template_creation.convert_and_evaluate(expression)                    
    
            oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 90°C")
            if oil_resistivity_mask.any():
                expression = table_oil.loc[oil_resistivity_mask, "VALUETEXT"][table_oil.loc[oil_resistivity_mask, "VALUETEXT"].index[0]]
                table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = template_creation.convert_and_evaluate(expression)
                
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


    ######################### Convert and Evaluate #########################
   
    @staticmethod
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
        

 
 ############################################### MAIN CLASS ###############################################       
    
    ######################### Main Function #########################

class pdf_main:
    def __init__(self, pdf_path, input_json, api_key):        
        self.input_json = input_json
        self.pdf_path = pdf_path
        self.LLM_functionalities = LLM_functionalities(api_key)
        self.Pdf_Process = Pdf_Process(pdf_path, input_json, api_key, relevant_page_level_dictionary)
        
 
    def extract_test_result_json(self):

        #Takes all the information out of the PDF.    
        related_data = self.Pdf_Process.finding_relevant_data()
        final_data_json = {}
        test_results = []
    
        print("Processing Tests...........")
        for test in related_data.keys():
            test_types = {}
            for i in self.Pdf_Process.input_json['selectedTests']:
                print("Processing Tests..........."+test)
                if i['test_type'] == test:
                    meta_data_json = i['meta_data']
                    tags_data_json = i['normal_data']
                    combined_json = meta_data_json | tags_data_json                
                    print(f'Working on {test}')                
                    data = related_data[test]
                    data = data.replace('[]', '')
                    test_types = {
                    "test_status": 0 if data else 1,
                    "test_description": "Success" if data else "No Relevant Data Found",
                    "test_type_code": i["test_type_code"],
                    "test_type": test,
                    "meta_data": {},
                    "normal_data": {}
                }                         
                    if data:
                        
                        print('Creating a structure with gpt 4o based on the given data')
                       
                        if test == 'Oil Testing':       
                            llm_oil_json = self.Pdf_Process.tag_check(combined_json)
                            modified_llm_model_prompts = llm_model_prompt_func(llm_oil_json)
                            prompt = modified_llm_model_prompts[test]
                            response = self.LLM_functionalities.model_data(data, prompt)
                            print('DGA template creation...')
#                            meta_data, normal_data = template_creation.DGA_template_creation(response, combined_json, meta_data_json) 
              
                            try:
                                meta_data, normal_data = template_creation.DGA_template_creation(response, combined_json, meta_data_json)
                                test_types["meta_data"] = meta_data
                                test_types["normal_data"] = normal_data
                            except:
                                test_types["test_status"] = 1
                                test_types["test_description"] = "Failed"

                        elif test == "Turns Ratio":
                            llm_turns_ratio_json = self.Pdf_Process.tag_check(combined_json)
                            response = self.LLM_functionalities.model_data(test, llm_model_prompt_func(llm_turns_ratio_json))
                            test_types["meta_data"] = meta_data_json
                            test_types["normal_data"] = {"Tap No": [], "Measured Ratio": [], "Calculated Ratio": []}

                    
                    test_results.append(test_types)
    
        final_data_json['asset_name'] = self.input_json['asset_name']
        final_data_json['asset_id'] = self.input_json['asset_id']
        final_data_json['opp_id'] = self.input_json['opp_id']
        final_data_json['odi_id'] = self.input_json['odi_id']
        final_data_json['report_type'] = self.input_json['report_type']
        final_data_json['tag_type'] = self.input_json['tag_type']
        final_data_json['selectedTests'] = test_results
         
        final_data_json["selectedTests"][test] = test_types

        return final_data_json

    
    ######################### Empty Result Function #########################
    
    def extract_empty_result_json(self, message):

        final_data_json = {}
        
        test_results = []
    
        print("Processing Empty Tests...........")
        for i in self.input_json['selectedTests']:
            test_types = {}
            meta_data_json = {}
            tags_data_json = {}
            if i['test_type'] == 'Oil Testing':                
                print('DGA template creation...')
                try:
                    meta_data,normal_data = {},{}
                    test_types["test_status"] = 1
                    test_types["test_description"] = message
                    test_types['test_type_code'] = i["test_type_code"]
                    test_types['test_type'] = 'Oil Testing'
                    test_types['meta_data'] = meta_data
                    test_types['normal_data'] = normal_data
                    test_results.append(test_types)
                except:
                    test_types["test_status"] = 1
                    test_types["test_description"] = message
                    test_results.append(test_types)
        final_data_json['asset_name'] = self.input_json['asset_name']
        final_data_json['asset_id'] = self.input_json['asset_id']
        final_data_json['opp_id'] = self.input_json['opp_id']
        final_data_json['odi_id'] = self.input_json['odi_id']
        final_data_json['report_type'] = self.input_json['report_type']
        final_data_json['tag_type'] = self.input_json['tag_type']
        final_data_json['selectedTests'] = test_results
        return final_data_json
