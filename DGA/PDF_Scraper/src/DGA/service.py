# system imports
import os
import sys
import logging
import requests
import json
import yaml
# Get the src directory (parent of current directory)
# src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if src_dir not in sys.path:
#     sys.path.insert(0, src_dir)
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
src_dir = os.path.dirname(current_dir) 
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# library imports
from dotenv import load_dotenv
load_dotenv()

# module imports
from utils.common_functions import encode_pdf_pages_to_base64, data_extract
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEPLOYMENT_URL = os.getenv('DEPLOYMENT_URL')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')

def load_config_files(): 
    try:
        response_format_json_path = os.path.join(current_dir, 'response_format_json.json')
        prompt_yaml_path = os.path.join(src_dir, 'prompts.yaml')
        prompt_path = os.path.join(current_dir, f'prompts\\dga_prompt.txt')
        # cwd = os.path.dirname(__file__)
        # prompt_path = os.path.join(cwd, f'prompts\\{dga_prompt}.txt')
        # response_format_path = os.path.join(cwd, 'dga_json.json')
        
        try:
            with open(prompt_path, 'r') as file:
                system_prompt = file.read()
                logger.info(f"Successfully loaded prompts.txt")
        except FileNotFoundError:
            logger.error(f"The file '{prompt_path}' was not found.")
            system_prompt = ""
        except Exception as e:
            logger.exception(f"Failed to load '{prompt_path}': {e}")
            system_prompt = ""

        try:
            with open(prompt_yaml_path, 'r') as file:
                extraction_prompt = yaml.safe_load(file)
                extraction_prompt = extraction_prompt['oil_testing']['extraction']['prompt']
                logger.info(f"Successfully loaded extraction_prompt")       
        except FileNotFoundError:
            logger.error(f"The file '{prompt_yaml_path}' was not found.")
            extraction_prompt = {}
        except Exception as e:
            logger.exception(f"Failed to load '{prompt_yaml_path}': {e}")
            extraction_prompt = {}

        try:
            with open(response_format_json_path, 'r') as file:
                response_format = json.load(file)
                logger.info(f"Successfully loaded response_format.json")
        except FileNotFoundError:
            logger.error(f"The file '{response_format_json_path}' was not found.")
            response_format = {}
        except Exception as e:
            logger.exception(f"Failed to load '{response_format_json_path}': {e}")
            response_format = {}

        return system_prompt, response_format, extraction_prompt    
    except Exception as e:
        logger.exception(f"Unexpected error in load_config_files: {e}")
        return "", {}

def json_normalization(model_response):
    """
    Normalizes the model response for Oil Testing reports.
    Returns a tuple: (normal_data, meta_data)
    """
    if not isinstance(model_response, dict):
        logger.error("Invalid input: model_response should be a dictionary.")
        return {}, {}

    logger.info(f"model_inference output: {model_response}")

    try:
        # If model gave explicit "meta_data", use it
        meta_data = model_response.get("meta_data", {})
        
        # List of known meta keys (adjust based on your prompt/output)
        known_meta_keys = [
            "Position", "Sampled By", "Sampling Method", 
            "Reason Of Sampling", "Atmospheric Condition",
            "Sampling Date", "Tested By"
        ]

        # Extract from model_response if not wrapped under "meta_data"
        for key in known_meta_keys:
            if key in model_response and key not in meta_data:
                meta_data[key] = model_response[key]

        # Everything else is normal_data (skip "meta_data" and known meta keys)
        normal_data = {
            k: v for k, v in model_response.items()
            if k != "meta_data" and k not in known_meta_keys
        }

        return normal_data, meta_data

    except Exception as e:
        logger.exception("Error in json_normalization for oil testing")
        return {}, {}

def create_mapped_json(input_json, normal_data, meta_data):
    """
    Maps the input_json to desired key format using normal_data and meta_data.
    Handles nested 'value' fields and maps to standard key names.
    """
    mapped_json = {
        "meta_data": {},
        "normal_data": {}
    }

    #  Map meta_data
    for raw_key, mapped_key in input_json.get("meta_data", {}).items():
        if raw_key in meta_data:
            value_obj = meta_data[raw_key]
            logger.debug(f"value_obj, {value_obj}")
            # Handle nested 'value' fields
            value = ""
            if isinstance(value_obj, dict):
                inner_val = value_obj.get("value")
                if isinstance(inner_val, dict):
                    value = inner_val.get("value", "")
                else:
                    value = inner_val
            logger.debug(f"mapped_key, {mapped_key}, value, {value}")
            mapped_json["meta_data"][mapped_key] = {
                "value": value
            }

    #  Map normal_data
    for raw_key, mapped_key in input_json.get("normal_data", {}).items():
        logger.debug(f"mapped_key, {mapped_key}, raw_key, {raw_key}")
        if raw_key in normal_data:
            entry = normal_data[raw_key]
            logger.debug(f"normal_data[raw_key]:, {normal_data[raw_key]}")
            mapped_json["normal_data"][mapped_key] = {
                "value": entry.get("value", ""),
                "test_method": entry.get("test_method", "")
            }
        else:
            logger.debug(f"{raw_key} not in normal_data")
    return mapped_json

def model_inference(pdf_path, pages,input_json):
    try:
        logger.info(f"Starting model inference for PDF: {pdf_path}, Pages: {pages}")
        data = encode_pdf_pages_to_base64(pdf_path, pages)    
        logger.debug(f"Encoded {len(data)} pages to base64 images.")  
        system_prompt, response_format, extraction_prompt = load_config_files()
        logger.debug("Loaded system prompt and response format.")
        markdown_data = data_extract(data,extraction_prompt)
        logger.debug("Extracted markdown data from base64 images.")

        api_url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        print('markdown data:', markdown_data)
        # for text input
        data = {
                "model": "gpt-4.1",
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": markdown_data}],
                "temperature": 0.1,
                "max_tokens": 3000,
                "tools": [response_format],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "oil_testing"}
            }
        }

        logger.info("Sending request to OpenAI API...")
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        logger.info("Received response from OpenAI API.")

        response_json = response.json()
        function_args = response_json['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        # print(function_args)
        parsed_output = json.loads(function_args)
        logger.info("Successfully parsed model output.")
        # Normalize output
        normal_data, meta_data = json_normalization(parsed_output)
        logger.info(f"Normalized output for DGA, {normal_data, meta_data}")      
        mapped_json = create_mapped_json(input_json, normal_data, meta_data)
        logger.info(f"Mapped json output for DGA, {mapped_json}")
        # try:
        #     with open(r"C:\Users\Admin\Rugged Monitoring\Narotham Reddy Sathigari - ML_Data Files\PDF_Scraper\DGA\outputs\dga_json.json", 'w') as f:
        #         json.dump(mapped_json, f, indent=4)
        #     print(f"output data successfully saved to file_path.")
        # except Exception as e:
        #     print(f"An error occurred while saving to JSON: {e}")
        return mapped_json['normal_data'], mapped_json['meta_data']
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request to OpenAI API failed: {e}")
        return {}
    except (KeyError, json.JSONDecodeError) as e:
        logger.exception(f"Failed to parse response JSON: {e}")
        return {}
    except Exception as e:
        logger.exception(f"Unexpected error during model inference: {e}")
        return {}
    
# pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\ML_Data Files\Offline Data\Cap_tan\two_winding\ET-BBC9G1-001 RLA.pdf" 
# pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\Pictures\format_pdfs\ET-BBZ9G3-01 DGA 22June2023.pdf"
# model_inference(pdf_path,[0,1,2],"dga_prompt")