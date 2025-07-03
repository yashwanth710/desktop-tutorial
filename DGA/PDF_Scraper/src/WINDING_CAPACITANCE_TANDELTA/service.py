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

#library imports
from dotenv import load_dotenv
load_dotenv()

# module imports
from utils.common_functions import encode_pdf_pages_to_base64, data_extract

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEPLOYMENT_URL = os.getenv('DEPLOYMENT_URL')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')

def load_config_files(winding_type): 
    try:
        response_format_json_path = os.path.join(current_dir, 'response_format_json.json')
        prompt_yaml_path = os.path.join(src_dir, 'prompts.yaml')
        prompt_path = os.path.join(current_dir, f'prompts\\{winding_type}.txt')
        try:
            with open(prompt_path, 'r') as file:
                system_prompt = file.read()
                logger.info(f"Successfully loaded prompts.txt for {winding_type}")
        except FileNotFoundError:
            logger.error(f"The file '{prompt_path}' was not found.")
            system_prompt = ""
        except Exception as e:
            logger.exception(f"Failed to load '{prompt_path}': {e}")
            system_prompt = ""

        try:
            with open(prompt_yaml_path, 'r') as file:
                extraction_prompt = yaml.safe_load(file)
                extraction_prompt = extraction_prompt['Winding_Cap_&_Tan_Delta_Measurement']['extraction']['prompt']
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
                if winding_type in ['autotransformer','two_winding']:
                    response_format = response_format['autotransformer']
                else:
                    response_format = response_format['three_winding']    
                logger.info(f"Successfully loaded response_format.json for {winding_type}")
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
    
def extract_meta_data_test_voltages(data, winding_type):
    meta_data = {}
    meta_data['Oil_Temperature'] = data.pop("Oil_Temperature", 0)
    if winding_type=="rectifier":
        ust_voltages = set()
        gst_voltages = set()
        for test_mode_key in ["UST", "GST-g", "GST"]:
            for measurement_key, measurements_list in data.items():
            # Iterate through the winding connection types within each test mode
#             for connection_key, measurements_list in data.items():
                if isinstance(measurements_list, list):
                    for measurement in measurements_list:
                        if "Test kV" in measurement:
                            test_kv = measurement["Test kV"]
                            if measurement_key.startswith("UST"):
                                ust_voltages.add(test_kv)
                            elif measurement_key.startswith("GST"):
                                gst_voltages.add(test_kv)
        meta_data["HVtestvoltages"] = sorted(list(ust_voltages))
        meta_data["LVtestvoltages"] = sorted(list(gst_voltages))
    elif winding_type=="three_winding":
        test_voltages = {
            f'{k}_voltages': set({item['Test kV'] for ele in v.values() for item in ele})
            for k, v in data.items()
            }
        meta_data.update(test_voltages)
    else:
        hv_voltages = set()
        lv_voltages = set()

        for test_mode_key in ["UST", "GST-g", "GST"]:
                if test_mode_key in data and isinstance(data[test_mode_key], dict):
                    test_mode_data = data[test_mode_key]
                    # Iterate through the winding connection types within each test mode
                    for connection_key, measurements_list in test_mode_data.items():
                        if isinstance(measurements_list, list):
                            for measurement in measurements_list:
                                if "Test kV" in measurement:
                                    test_kv = measurement["Test kV"]
                                    if connection_key.startswith("HV"):
                                        hv_voltages.add(test_kv)
                                    elif connection_key.startswith("LV"):
                                        lv_voltages.add(test_kv)
        meta_data["HVtestvoltages"] = sorted(list(hv_voltages))
        meta_data['LVtestvoltages'] = sorted(list(lv_voltages))                               
    logger.debug(f"Extracted metadata details, {meta_data}")
    return meta_data

def json_normalization(model_response, winding_type):
    """
    Transforms a model response nested JSON string into a flattened JSON structure.

    Args:
        input_json_str (str): The input JSON string in the response output format.
        winding_type (str): This gives information about winding_type.
    Returns:
        str: A JSON string representing the flattened data.
               Returns an empty JSON string if input is invalid.
    """
    if not isinstance(model_response, dict):
        print("Error: Input must be a dictionary.")
        return {}
    logger.info(f"model_inference output:, {model_response}") 
    logger.info(f"type output:, {winding_type}") 
    meta_data = extract_meta_data_test_voltages(model_response, winding_type)

    normal_data = {}
    # Mapping for the measurement keys to tags short cut
    key_mapping = {
        "Test kV": "KV",
        "Capacitance (pF)": "CAP",
        "Tan delta (%)": "TAND",
        "Power Loss (Watts)": "WATTS",
        "Current (mA)": "MA"
    }
    # Iterate through the main categories (e.g., "HV", "LV")
    for main_category_key, sub_categories in model_response.items():
        # Iterate through sub-categories (e.g., "UST-A", "UST-B")
        for sub_category_key, test_results_list in sub_categories.items():
            # Iterate through each test result dictionary in the list
            for i, test_result_dict in enumerate(test_results_list):
                if winding_type=="two_winding" or winding_type=="three_winding":
                    if i==0:
                        test_voltage_level_suffix = f"AT-MIN-TV"
                    elif i==2:
                        test_voltage_level_suffix = f"AT-MAX-TV"
                    else:    
                        test_voltage_level_suffix = f"AT-TV{i + 1}"
                else:
                    test_voltage_level_suffix = f"AT-TV{i + 1}"        

                for measurement_key, value in test_result_dict.items():
                    if measurement_key in key_mapping:
                        short_measurement_key = key_mapping[measurement_key]
                        
                        if winding_type=="three_winding":
                            new_key = f"{main_category_key}-{sub_category_key}-{short_measurement_key}-{test_voltage_level_suffix}"
                        else:
                            new_key = f"{sub_category_key}-{main_category_key}-{short_measurement_key}-{test_voltage_level_suffix}"
                        # Handle empty strings for Power Loss and Current, convert to None
                        if value == "":
                            normal_data[new_key] = None
                        else:
                            normal_data[new_key] = value
                    else:
                        logger.debug(f"Warning: Unexpected measurement key '{measurement_key}' found. Skipping.")
    
    return normal_data, meta_data

def create_mapped_json(input_json, normal_data, meta_data):
    """
    Create a new JSON by mapping values from input_json as keys 
    and corresponding values from result_json as values
    """
    result_json = {"meta_data": meta_data,
                   "normal_data": normal_data}
    mapped_json = {"meta_data": {}, "normal_data": {}}
    
    # meta_data section
    for input_key, input_value in input_json["meta_data"].items():
        if input_value is not None:
            if input_key in result_json["meta_data"]:
                mapped_json["meta_data"][input_value] = result_json["meta_data"][input_key]
    
    # normal_data section
    for input_key, input_value in input_json["normal_data"].items():
        if input_value is not None:
            # Finding corresponding key in result_json
            if input_key in result_json["normal_data"]:
                if result_json["normal_data"][input_key] is not None:
                    mapped_json["normal_data"][input_value] = result_json["normal_data"][input_key]
            else:
                logger.debug(f"Some AI service generated keys ar missing in input json,{input_key}")
    
    return mapped_json

def model_inference(pdf_path, pages, winding_type, input_json):
    """
    Args:
        pdf_path (str): Input path location to read pdf file
        pages (list): This gives information pages to search for
        winding_type (str): This gives information about winding_type
        input_json (dict): This is input json received through api for respective tests.
    Returns:
        str: A JSON string representing the flattened data.
               Returns an empty JSON string if input is invalid.
    
    """
    logger.info(f"relevant pages: {pages}")
    try:
        logger.info(f"Starting model inference for PDF: {pdf_path}, Pages: {pages}")
        data = encode_pdf_pages_to_base64(pdf_path, pages)    
        logger.debug(f"Encoded {len(data)} pages to base64 images.")  
        logger.debug(f"Encoded images character sizes: {[len(i) for i in data]}")
        system_prompt, response_format, extraction_prompt = load_config_files(winding_type)
        logger.debug("Loaded system prompt , response format and extraction_prompt.")
        markdown_data = data_extract(data, extraction_prompt)
        logger.debug("Extracted markdown data from base64 images.")

        # api_url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {AZURE_OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
                "model": "gpt-4.1",
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": markdown_data}],
                "temperature": 0.1,
                "max_tokens": 5000,
                "tools": [response_format],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "winding_capacitance_test_data"}
            }
        }

        logger.info("Sending request to OpenAI API...")
        response = requests.post(DEPLOYMENT_URL, headers=headers, json=data)
        response.raise_for_status()
        logger.info("Received response from OpenAI API.")
        
        response_json = response.json()     
        function_args = response_json['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        logger.debug(f"Model Response Json Format: {function_args}")
        
        parsed_output = json.loads(function_args)
        logger.info("Successfully parsed model output.")

        normal_data, meta_data = json_normalization(parsed_output, winding_type)
        # logger.info(f"Normalized output for tanDeltaCapacitanceResult, {normal_data, meta_data}") 
        mapped_json = create_mapped_json(input_json, normal_data, meta_data)
        logger.info(f"Mapped json output for tanDeltaCapacitanceResult, {mapped_json}") 
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
    
# pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\ML_Data Files\Offline Data\Cap_tan\two_winding\ET-BBC9G1-001 RLA.pdf" #twowinding
# pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\ML_Data Files\Offline Data\Cap_tan\FAT report After SCT for Power Transformer Sr. No. 2020035004.pdf"  #autotransfomer
# # pdf_path = r"C:\Users\Admin\OneDrive - Rugged Monitoring\ML_Data Files\Offline Data\Cap_tan\three_winding\Report-1_2025810_Unit-30 - UT-A.pdf"  #three_winding
# model_inference(pdf_path,[8],'autotransformer')