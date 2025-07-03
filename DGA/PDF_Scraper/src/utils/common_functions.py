# system imports
import os
import sys
import base64
import json
import yaml
import requests
from io import BytesIO
import logging
from concurrent.futures import ThreadPoolExecutor

# library imports
import fitz
import numpy as np
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

# module/file imports
# yaml_file, response_format_json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
src_dir = os.path.dirname(current_dir) 
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm_model = os.getenv("llm_model")
DEPLOYMENT_URL = os.getenv('DEPLOYMENT_URL')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')

prompt_yaml_path = os.path.join(src_dir, 'prompts.yaml')
response_format_json_path = os.path.join(src_dir, 'function_schema.json')

# logging.info(f"{current_dir},\n,{src_dir}")
# logging.info(f"{prompt_yaml_path},\n,{response_format_json_path}")
try:
    try:
        with open(prompt_yaml_path, 'r') as file:
                yaml_file = yaml.safe_load(file)
                # extraction_prompt = extraction_prompt['Winding_Cap_&_Tan_Delta_Measurement']['extraction']['prompt']
                logger.info(f"Successfully loaded extraction_prompt")       
    except FileNotFoundError:
        logger.error(f"The file '{prompt_yaml_path}' was not found.")
        yaml_file = {}
    except Exception as e:
        logger.exception(f"Failed to load '{prompt_yaml_path}': {e}")
        yaml_file = {}

    try:
        with open(response_format_json_path, 'r') as file:
                response_format_json = json.load(file)
                # extraction_prompt = extraction_prompt['Winding_Cap_&_Tan_Delta_Measurement']['extraction']['prompt']
                logger.info(f"Successfully loaded response_format_json")       
    except FileNotFoundError:
        logger.error(f"The file '{response_format_json_path}' was not found.")
        response_format_json = {}
    except Exception as e:
        logger.exception(f"Failed to load '{response_format_json_path}': {e}")
        response_format_json = {}
except Exception as e:
    logger.exception(f"Unexpected error occured while loading search mechanism config files: {e}")    

# pdf_path = r"C:\Users\Admin\Rugged Monitoring\Narotham Reddy Sathigari - ML_Data Files\Offline Data\Offline data reports(mostly oil)\MPS\Format - 1\2022 - 007.pdf"
def encode_pdf_pages_to_base64(pdf_path, selected_pages=None):
    """Convert specific PDF pages to base64 images.
    Arguments: pdf_path: string
               pages: list[int]"""
    base64_images = []
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"{doc.page_count},countttt")
        # selected_pages = pages if pages else range(len(doc))
        logger.debug(f"Selected pages: {selected_pages}")

        for page_num in selected_pages:
            page = doc.load_page(int(page_num))
            pix = page.get_pixmap(dpi=600)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            base64_images.append(img_b64)
        logger.info(f"Successfully converted {len(base64_images)} pages to base64.")    
        return base64_images
    
    except Exception as e:
        logger.exception(f"Error processing PDF: {e}")
        return []
 

def data_extract(base64_images, extraction_prompt):
    markdown_data = ""
    # if llm_model == 'gpt':
    #     model_name ='gpt-4.1'
    #     api_url = "https://api.openai.com/v1/chat/completions"
    #     API_KEY = OPENAI_API_KEY
    # elif llm_model == 'mixtral':
    #     model_name = "pixtral-12b-latest"   
    #     api_url = "https://api.mistral.ai/v1/chat/completions"
    #     API_KEY = MISTRAL_API_KEY 
    # else:
    #     logger.error(f"Unsupported model: {llm_model}")    
    # logger.info(f"Selected model name: {model_name}")

    for idx, base64_image in enumerate(base64_images):
        if base64_image:
            logger.info(f"Processing base64 image {idx + 1}/{len(base64_images)}")
            base64_data_url = f"data:image/jpeg;base64,{base64_image}"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_data_url}
                        }
                    ]
                }
            ]
            headers = {
                "Authorization": f"Bearer {AZURE_OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4.1",
                "messages": messages
            }

            try:
                # Send the POST request to Mistral's API
                response = requests.post(
                    DEPLOYMENT_URL,
                    headers=headers,
                    json=data
                )

                # Check if the request was successful
                response.raise_for_status()
                # Parse the response
                chat_response = response.json()
                # print(chat_response['choices'][0]['message']['content'])
                markdown_result = chat_response['choices'][0]['message']['content']
                logger.info(f"markdown_result of page {idx + 1}: {markdown_result}")
                markdown_data += markdown_result
                logger.debug(f"Received markdown for image {idx + 1}")

            except requests.exceptions.RequestException as e:
                logger.exception(f"Request to Vision API failed: {e}")
                return {}
            except Exception as e:
                logger.exception(f"Error in processing the Vision API on image {idx + 1}: {e}")

    logger.info("Completed data extraction from all images.")
    return markdown_data

def parse_page_ranges(page_input):
    if not page_input or not page_input.strip():
        return []
    
    pages = set()
    parts = page_input.strip().split(',')
    logger.info(f"User provided pages, {parts}")
    for part in parts:
        part = part.strip()
        print("part",part)
        if not part:
            continue
            
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())
            print(start, end)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    pages = [i-1 for i in pages]
    logger.debug(f"User provided page numbers: {pages}")
    return sorted(list(pages))

def mistral_call(doc, split_pages, yaml_file, response_format_json):    
    relevant_pages = {}
    # try:
    for page in split_pages:
        logger.debug(f'Base64 conversion started for the page')
        single_page = doc.load_page(int(page))            
        pix = single_page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        logger.debug(f'Base64 conversion ended for the page')

        #Pixtral Model Calling
        # url = 'https://api.mistral.ai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {AZURE_OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': "gpt-4.1",
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': yaml_file['search_pages']['prompt']
                        }, 
                        {
                            'type': 'image_url',
                            'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}
                        }
                    ]
                }
            ],
            'tools':[response_format_json['function_schema']],
            'tool_choice': {
                "type": "function",
                "function": {
                    "name": "search_data_presence"
                }
                }
            }
        success = False
        while not success:
            try:
                response = requests.post(DEPLOYMENT_URL, headers=headers, json=data)                
                output = json.loads(response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments'])
                success = True
                for test_name, value in output.items():
                    if test_name not in relevant_pages:
                        relevant_pages[test_name] = []
                    if value == 'Yes':                           
                        relevant_pages[test_name].append(page)
            except Exception as e:
                print(f"Error with Mistral API: {e}")
    # except Exception as e:
    #         print(f"Error: {e}")
    return relevant_pages

def search_pages_mechanism(input_json):
    logger.info("Search for relevant pages initiated.")
    doc = fitz.open(input_json['path'])
    given_tests = [test['test_type'] for test in input_json['selectedTests']]
    count_page_test = 0
    overall_pages = []
    test_pages = {}
    for test in input_json['selectedTests']:
        if test['pages']:
            count_page_test = count_page_test + 1
            list_pages = parse_page_ranges(test['pages'])
            test_pages[test['test_type']] = list_pages
            for page in list_pages:
                if page not in overall_pages:
                    overall_pages.append(page)        

    if len(given_tests) == count_page_test:
        # print('check', test_pages)
        split_pages = np.array_split(list(sorted(overall_pages)), 3)
        logger.debug(f"Pages of all the given tests are split into: {split_pages}")

    elif len(given_tests) > count_page_test:
        split_pages = np.array_split(list(range(doc.page_count)), 3)
        logger.debug(f"Pages of entire document are split into: {split_pages}")

    print('split_pages:', split_pages)
    with ThreadPoolExecutor(max_workers=3) as executor:
        logger.info("Initiating concurrent page search using ThreadPoolExecutor for all given tests.")
        futures = [executor.submit(mistral_call, doc, split, yaml_file, response_format_json) for split in split_pages]
        logger.info("Finished concurrent page search using ThreadPoolExecutor for all given tests.")
        # futures = []
        # for test, pages in test_pages.items():
        #     futures.append(executor.submit(mistral_call, doc, pages, function_schema, test, test_jsons))

    output_list = [f.result() for f in futures]
    test_relevant_pages = {}
    for thread in output_list:
        for test, values in thread.items():
            if test in given_tests:            
                if test not in test_relevant_pages:
                    test_relevant_pages[test] = []
                for value in values:
                    test_relevant_pages[test].append(value)
    logger.info(f"Relevant pages for all the given tests after searching are {test_relevant_pages}")
    return test_relevant_pages



# pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\Pictures\format_pdfs\ET-GYG941-001A DGA.pdf"
# data = encode_pdf_pages_to_base64(pdf_path, pages=[0])      
# markdown_data = data_extract(data)
# print(markdown_data) 