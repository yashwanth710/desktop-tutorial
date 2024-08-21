# llm functionality
# Json creation(template)
from datetime import datetime
from openai import OpenAI
from langchain_openai import ChatOpenAI
from prompts import llm_model_prompts, DGA_template_creation
import os
from pdf_processing import finding_relevant_data
import json 
import pandas as pd
import re
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
    end_time = datetime.now()
#     print('Duration: {}'.format(end_time - start_time))
    
    return response


#################### Main Function #########################

def extract_test_result_json(input_json, pdf_path):
    related_data = finding_relevant_data(input_json, pdf_path)
    
    final_data_json = {}
    for test in related_data.keys():
        # no relavant data
        prompt = llm_model_prompts[test]
        data = related_data[test]
        if not data:
            final_data_json[test] = {"status":False, "message": "No Relevant Data Found"}
        else:
            response = model_data(data, prompt)
            if test == 'Oil Testing':
                DGA = DGA_template_creation(response)
                print(type(DGA), 'sadddddddddddddddddddddddddddddddddddddddddddddddddddddddd')
                final_data_json[test] = DGA.to_dict('records')
            else:
                final_data_json[test] = response
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