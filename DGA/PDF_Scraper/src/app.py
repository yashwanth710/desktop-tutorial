# system imports
import os
import sys
import json
import yaml
import fitz
import logging
import threading
import uuid

# library imports
from flask import Flask, request, jsonify

# module imports
from redis_client import RedisClient
from WINDING_CAPACITANCE_TANDELTA.service import model_inference as winding_inference
from DGA.service import model_inference as oil_inference
from utils.common_functions import search_pages_mechanism
from TURNS_RATIO.service import model_inference as turns_inference
# Logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Redis connection
QUEUE_NAME = os.environ.get('QUEUE_NAME')
try:
    write_redis = RedisClient(os.environ.get("REDIS_IP"), os.environ.get("REDIS_PORT"))
    logger.info(f"Successfully connected to Redis:\n Redis IP: {os.environ.get('REDIS_IP')} \n REDIS PORT: {os.environ.get('REDIS_PORT')},\n QUEUE NAME: {QUEUE_NAME}")
except Exception as e:
    logger.exception("Failed to connect to Redis server..")

@app.route("/ODI/check")
def check():
    logger.info("ODI Service Is Online..!")
    return {"message": "ODI Service Is Online..!"}

task_results_store = {}

def _process_all_tests_in_background(task_id, original_input_json):
    """
    Performs the heavy lifting of processing tests in the background.
    Updates the global task_results_store with status and results.
    """
    logger.info(f"Background task {task_id}: Starting processing.")
    
    # Create a deep copy to ensure modifications don't affect the original object
    import copy
    processing_input_json = copy.deepcopy(original_input_json)
    
    try:
        # Update task status to "running"
        task_results_store[task_id] = {"status": "running", "progress": "Initializing"}

        # Search Page Mechanism
        relevant_pages = search_pages_mechanism(processing_input_json)
        # relevant_pages = {"Winding Tan Delta and Capacitance": [10,11]}
        logger.debug(f"Background task {task_id}: Relevant pages found: {relevant_pages}")
        task_results_store[task_id]["progress"] = "Pages searched"

        # Loop through each selected test to process
        for idx, test in enumerate(processing_input_json.get('selectedTests', [])):
            test_type = test.get('test_type')
            # pages = test.get("pages")
            
            # Initialize test status and description
            test["test_status"] = False
            test["test_description"] = "Not processed or unsupported test type."

            task_results_store[task_id]["progress"] = f"Processing {test_type} ({idx+1}/{len(processing_input_json['selectedTests'])})"
            logger.debug(f"Processing {test_type} ({idx+1}/{len(processing_input_json['selectedTests'])}")
            # if not pages:
            #     logger.warning(f"Background task {task_id}: Test type '{test_type}' has no pages defined.")
            #     test["test_description"] = "No pages defined for this test type."
            #     continue # Skip to the next test if no pages
            
            try:
                if test_type == "Oil Testing":
                    if not relevant_pages[test_type]:
                        logger.warning(f"Background task {task_id}: Test type '{test_type}' has no pages defined.")
                        test["test_status"] = False
                        test["test_description"] = "No pages defined for this test type."
                        continue
                    else:
                        logger.info(f"Background task {task_id}: Calling model_inference for Oil Testing test.")
                        retrieved_normal_data, retrieved_meta_data = oil_inference(
                            processing_input_json["path"], relevant_pages[test_type], test
                        )
                        test["meta_data"] = retrieved_meta_data
                        test["normal_data"] = retrieved_normal_data
                        test["test_status"] = True
                        test["test_description"] = "Successfully Processed Oil Testing Data."

                elif test_type == "Winding Tan Delta & Capacitance":
                    if not relevant_pages[test_type]:
                        logger.warning(f"Background task {task_id}: Test type '{test_type}' has no pages defined.")
                        test["test_status"] = False
                        test["test_description"] = "No pages defined for this test type."
                        continue
                    else:
                        winding_type = test.get("type")
                        logger.info(f"Background task {task_id}: Calling model_inference for Winding Tan Delta and Capacitance teset.")    
                        retrieved_normal_data, retrieved_meta_data = winding_inference(
                            processing_input_json["path"], relevant_pages[test_type], winding_type, test
                        )
                        test["meta_data"] = retrieved_meta_data
                        test["normal_data"] = retrieved_normal_data
                        test["test_status"] = True
                        test["test_description"] = "Successfully Processed Winding Tan Delta and Capacitance Data."

                elif test_type == "Turns Ratio":
                     if not relevant_pages[test_type]:
                        logger.info(f"Background task {task_id}: Processing Turns Ratio test (placeholder).")
                        test["normal_data"] = {"Turns Ratio Data": "Processed"}
                        test["test_status"] = False
                        test["test_description"] = "Successfully Processed Turns Ratio Data (Placeholder)."
                        continue                        
                     else:
                       turns_type = test.get("type")
                       logger.info(f"Background task {task_id}: Calling model_inference for Oil Testing test.")
                     retrieved_normal_data = turns_inference(
                     processing_input_json["path"], relevant_pages[test_type],turns_type,test
                        )
                test["normal_data"] = retrieved_normal_data
                test["test_status"] = True
                test["test_description"] = "Successfully Processed TURNS RATIO Data."
                continue

            except Exception as e:
                test["test_status"] = False
                test["test_description"] = f"Failed processing {test_type} data: {str(e)}"
                logger.exception(f"Background task {task_id}: Error processing {test_type}.")
                # Continue to next test even if one fails

        # All tests processed (or attempted)
        task_results_store[task_id]["status"] = True
        task_results_store[task_id]["result"] = processing_input_json # Store the final processed JSON
        try: 
            write_redis.rpush(QUEUE_NAME,json.dumps(processing_input_json))
        except Exception as e:
            logger.exception(f"Failed to update data in Redis,{e}")    

    except Exception as e:
        logger.exception(f"Background task {task_id}: An unhandled error occurred during processing.")
        task_results_store[task_id]["status"] = False
        task_results_store[task_id]["error"] = e
        try: 
            write_redis.rpush(QUEUE_NAME, json.dumps(processing_input_json))
        except Exception as e:
            logger.exception(f"Failed to update data in Redis,{e}")
    finally:
        logger.info(f"Background task {task_id}: Finished processing.")

@app.route("/ODI/intiate_file_processing", methods=['POST'])
def intiate_file_processing():
    """
    Validate inputs from JSON, initiate test-specific processing in background,
    and return an immediate acknowledgement.
    """
    input_json = request.get_json()
    logger.debug(f"Received input: {input_json}")

    # --- Input Validation ---
    if not input_json:
        return jsonify({"error": "Invalid JSON payload.", "status": False}), 400
    
    # Check if 'path' exists
    if not os.path.exists(input_json.get("path", "")):
        logger.warning("Invalid file path provided.")
        return jsonify({"error": "The provided path does not exist.", "status": False}), 400

    # Check 'normal_data' in selectedTests
    for test in input_json.get('selectedTests', []):
        if "normal_data" in test:
            value = test["normal_data"]
            if not value: # Catches None or empty dict {}
                logger.error("normal_data exists but is empty or None.")
                return jsonify({"status":False, "message":"Error: normal_data exists but value is invalid (None or empty dict)"}), 400

    # --- Initiate Background Processing ---
    task_id = str(uuid.uuid4())
    task_results_store[task_id] = {"status": "pending"} 

    thread = threading.Thread(
        target=_process_all_tests_in_background,
        args=(task_id, input_json)
    )
    thread.daemon = True # Allows the main program to exit even if threads are running
    thread.start()

    return jsonify({
        "status": True,
        "message": "File processing started in the background.",
        "task_id": task_id
    }), 202 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5010, debug=True)