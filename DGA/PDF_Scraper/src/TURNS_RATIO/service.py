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


def load_config_files(autotransformer): 
    try:
        response_format_json_path = os.path.join(current_dir, 'response_format_json.json')
        prompt_yaml_path = os.path.join(src_dir, 'prompts.yaml')
        prompt_path = os.path.join(current_dir, f'prompts\\{autotransformer}.txt')
        # cwd = os.path.dirname(__file__)
        # prompt_path = os.path.join(cwd, f'prompts\\{dga_prompt}.txt')
        # response_format_path = os.path.join(cwd, 'dga_json.json')
        
        try:
            with open(prompt_path, 'r') as file:
                system_prompt = file.read()
                logger.info(f"Successfully loaded prompts.txt for {autotransformer}")
        except FileNotFoundError:
            logger.error(f"The file '{prompt_path}' was not found.")
            system_prompt = ""
        except Exception as e:
            logger.exception(f"Failed to load '{prompt_path}': {e}")
            system_prompt = ""

        try:
            with open(prompt_yaml_path, 'r') as file:
                extraction_prompt = yaml.safe_load(file)
                extraction_prompt = extraction_prompt['turns_ratio']['extraction']['prompt']
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
                if autotransformer in ['autotransformer']:
                    response_format = response_format['autotransformer']  
                logger.info(f"Successfully loaded response_format.json for {autotransformer}")
        except FileNotFoundError:
            logger.error(f"The file '{response_format_json_path}' was not found.")
            response_format = {}
        except Exception as e:
            logger.exception(f"Failed to load '{response_format_json_path}': {e}")
            response_format = {}    

        return system_prompt, response_format, extraction_prompt    
    except Exception as e:
        logger.exception(f"Unexpected error in load_config_files: {e}")
        return {}, {}, {}


def model_output(pdf_path, pages, autotransformer):
    try:
        logger.info(f"Starting model inference for PDF: {pdf_path}, Pages: {pages}")
        
        # Step 1: Encode PDF and extract text
        encoded_data = encode_pdf_pages_to_base64(pdf_path, pages)
        markdown_data = data_extract(encoded_data)
        system_prompt, response_format, _ = load_config_files(autotransformer)

        # Step 2: Build OpenAI request
        payload = {
            "model": "gpt-4.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_data}
            ],
            "temperature": 0.1,
            "max_tokens": 3000,
            "tools": response_format if isinstance(response_format, list) else [response_format],
            "tool_choice": {
                "type": "function",
                "function": {"name": "turns_ratio_test"}
            }
        }

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Step 3: Send API request
        logger.info("Sending request to OpenAI API...")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        # Step 4: Parse response
        function_args = response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        parsed_output = json.loads(function_args)
        logger.info("Successfully parsed model output.")

        print("Model Output:\n")
        print(json.dumps(parsed_output, indent=4))

        return parsed_output

    except Exception as e:
        logger.exception(f"Model inference failed: {e}")
        return {}


def json_normalization(model_output):
    """
    Transforms model output into a flattened dictionary with composite keys.
    The format is: <main_key>_TAP<tap_number>_<mapped_data_key>: value
    """
    normal_data = {}

    # Define replacements for keys
    key_mapping = {
        "CALCULATED RATIO": "CALC_VOL_RATIO",
        "MEASURED RATIO": "MES_VOL_RATIO"
    }

    for main_key, main_value_list in model_output.items():
        for data_entry in main_value_list:
            tap_value = data_entry.get("TAPNO", None)
            for k, v in data_entry.items():
                if k == "TAPNO":
                    continue  # Skip TAPNO key

                # Use mapped key if present
                mapped_k = key_mapping.get(k, k)

                # Construct final tag name
                tag_name = f"{main_key}_{mapped_k}_TAP{tap_value}"
                normal_data[tag_name] = v

    return {"normal_data": normal_data}

def create_mapped_json(input_json, result_json):
    """
    Create a mapped JSON using input_json keys as lookup keys in result_json["normal_data"],
    and input_json values as final output keys.
    """
    mapped_json = {"normal_data": {}}

    normal_data = result_json.get("normal_data", {})  # safely get flat data

    # Handle both wrapped and flat versions of input_json
    if "normal_data" in input_json:
        input_pairs = input_json["normal_data"].items()
    else:
        input_pairs = input_json.items()

    for input_key, output_key in input_pairs:
        if output_key is not None:
            if input_key in normal_data:
                if normal_data[input_key] is not None:
                    mapped_json["normal_data"][output_key] = normal_data[input_key]
        
    return mapped_json


def model_inference(pdf_path, pages, autotransformer, input_json):
    """
    Args:
        pdf_path (str): Path to the PDF file.
        pages (list): Page numbers to extract from the PDF.
        autotransformer (str): Type of transformer (e.g., 'autotransformer').
        input_json (dict): Input JSON passed from the API.

    Returns:
        Tuple[dict, dict]: normal_data (meta_data can be empty if not applicable).
    """
    logger.info(f"Starting model inference for PDF: {pdf_path}, Pages: {pages}")
    
    try:
        # Step 1: PDF to base64 and markdown extraction
        data = encode_pdf_pages_to_base64(pdf_path, pages)    
        logger.debug(f"Encoded {len(data)} pages to base64 images.")  
        logger.debug(f"Encoded images character sizes: {[len(i) for i in data]}")
        
        system_prompt, response_format,extraction_prompt = load_config_files(autotransformer)
        logger.debug("Loaded system prompt response format and extraction_prompt.")
        
        markdown_data = data_extract(data,extraction_prompt)
        logger.debug("Extracted markdown data from base64 images.")

        # Step 2: Prepare request
        headers = {
            "Authorization": f"Bearer {AZURE_OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": markdown_data}
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "tools": [response_format],
            "tool_choice": {
                "type": "function",
                "function": {"name": "turns_ratio_test"}
            }
        }

        # Step 3: API call
        logger.info("Sending request to OpenAI API...")
        response = requests.post(DEPLOYMENT_URL, headers=headers, json=payload)
        response.raise_for_status()
        logger.info("Received response from OpenAI API.")

        # Step 4: Parse and normalize
        function_args = response.json()['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        logger.debug(f"Model Response JSON: {function_args}")
        
        parsed_output = json.loads(function_args)
        logger.info("Successfully parsed model output.")

        normal_data = json_normalization(parsed_output)
        logger.info(f"Normalized turns ratio output: {normal_data}")

        mapped_json = create_mapped_json(input_json, normal_data)
        logger.info(f"Mapped turns ratio JSON: {mapped_json}")

        return mapped_json.get('normal_data') 
    
      
    except requests.exceptions.RequestException as e:
        logger.exception("Request to OpenAI API failed.")
        return {}, {}
    except (KeyError, json.JSONDecodeError) as e:
        logger.exception("Failed to parse response JSON.")
        return {}, {}
    except Exception as e:
        logger.exception("Unexpected error during model inference.")
        return {}, {}
