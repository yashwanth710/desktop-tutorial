# llm functionality
# Json creation(template)
from datetime import datetime
from openai import OpenAI
from langchain_openai import ChatOpenAI
from prompts import llm_model_prompt_func
from pdf_processing import DGA_template_creation, tag_check
import os
from pdf_processing import finding_relevant_data
import pandas as pd
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

os.environ["OPENAI_API_KEY"] = "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"

# Initialize the OpenAI GPT-4 model for chat

def model_data(data, prompt):    
    # Initialize the OpenAI GPT-4 model for chat
    chat_llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    # Combine the query and document content
    combined_query = prompt + "\n\nDocument Content:\n" + data
    start_time = datetime.now()

    # Generate a completion
    response = chat_llm.predict(text=combined_query) # Use predict() instead of chat() for ChatOpenAI
    # end_time = datetime.now()
#     print('Duration: {}'.format(end_time - start_time))
    
    return response


#################### Main Function #########################

def extract_test_result_json(input_json, pdf_path):

    #Takes all the information out of the PDF.
    related_data = finding_relevant_data(input_json, pdf_path)

    final_data_json = {}
    
    test_results = []

    print("Processing Tests...........")
    for test in related_data.keys():
        test_types = {}
        for i in input_json['selectedTests']:
            print("Processing Tests..........."+test)
            if i['test_type'] == test:
                meta_data_json = i['meta_data']
                tags_data_json = i['normal_data']
                combined_json = meta_data_json | tags_data_json
                print(f'Working on {test}')
                llm_oil_json = tag_check(combined_json)
                modified_llm_model_prompts = llm_model_prompt_func(llm_oil_json)
                prompt = modified_llm_model_prompts[test]
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
                    response = model_data(data, prompt)
                    if test == 'Oil Testing':                
                        print('DGA template creation...')
                        try:
                            meta_data, normal_data = DGA_template_creation(response, combined_json, meta_data_json)                        
                            test_types["meta_data"] = meta_data
                            test_types["normal_data"] = normal_data
                        except:
                            test_types["test_status"] = 1
                            test_types["test_description"] = "Failed"
                
                test_results.append(test_types)


                # print(data, 'DATAAAAAAAAAAAAAAA')
                # if not data:
                #     final_data_json[test] = {"status":False, "message": "No Relevant Data Found"}
                # else:
                #     print('Creating a structure with gpt 4o based on the given data')
                #     response = model_data(data, prompt)
                #     if test == 'Oil Testing':                
                #         print('DGA template creation...')
                #         try:
                #             meta_data,normal_data = DGA_template_creation(response, combined_json, meta_data_json)
                #             test_types["test_status"] = 0
                #             test_types["test_description"] = "Success"
                #             test_types['test_type_code'] = i["test_type_code"]
                #             test_types['test_type'] = test
                #             test_types['meta_data'] = meta_data
                #             test_types['normal_data'] = normal_data
                #             test_results.append(test_types)
                #         except:
                #             test_types["test_status"] = 2
                #             test_types["test_description"] = "Failed"
                            

                        # meta_data = {key: DGA[key] for key in meta_data_json if key in DGA}
                        # normal_data = {key: DGA[key] for key in tags_data_json if key in DGA}

                    # else:
                    #     test_results.append(response)
    final_data_json['asset_name'] = input_json['asset_name']
    final_data_json['asset_id'] = input_json['asset_id']
    final_data_json['opp_id'] = input_json['opp_id']
    final_data_json['odi_id'] = input_json['odi_id']
    final_data_json['report_type'] = input_json['report_type']
    final_data_json['tag_type'] = input_json['tag_type']
    final_data_json['selectedTests'] = test_results
    return final_data_json


def extract_empty_result_json(input_json, pdf_path,message):

    final_data_json = {}
    
    test_results = []

    print("Processing Empty Tests...........")
    for i in input_json['selectedTests']:
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
                test_types['test_type'] = test
                test_types['meta_data'] = meta_data
                test_types['normal_data'] = normal_data
                test_results.append(test_types)
            except:
                test_types["test_status"] = 1
                test_types["test_description"] = message
                test_results.append(test_types)
    final_data_json['asset_name'] = input_json['asset_name']
    final_data_json['asset_id'] = input_json['asset_id']
    final_data_json['opp_id'] = input_json['opp_id']
    final_data_json['odi_id'] = input_json['odi_id']
    final_data_json['report_type'] = input_json['report_type']
    final_data_json['tag_type'] = input_json['tag_type']
    final_data_json['selectedTests'] = test_results
    return final_data_json



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
# pdf_path = r"C:\Users\Admin\Desktop\New folder\2018 - 001.pdf"
# print(extract_test_result_json(input_json, pdf_path)) 