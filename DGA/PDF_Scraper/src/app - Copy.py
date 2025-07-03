# ------------------------
# FastAPI Version of Your Flask App (Full Conversion)
# ------------------------

import os
import sys
import json
import yaml
import fitz
import copy
import uuid
import logging
from typing import Dict, Any


from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ------------------------
# Module imports
# ------------------------
from redis_client import RedisClient
from WINDING_CAPACITANCE_TANDELTA.service import model_inference as winding_inference
from DGA.service import model_inference as oil_inference
from TURNS_RATIO.service import model_inference as turns_inference
from utils.common_functions import search_pages_mechanism

# ------------------------
# Logging setup
# ------------------------
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------------
# App Initialization
# ------------------------
app = FastAPI()

# ------------------------
# Redis Setup
# ------------------------
QUEUE_NAME = os.environ.get("QUEUE_NAME")
try:
    write_redis = RedisClient(os.environ.get("REDIS_IP"), os.environ.get("REDIS_PORT"))
    logger.info(f"Connected to Redis. IP: {os.environ.get('REDIS_IP')}, PORT: {os.environ.get('REDIS_PORT')}, QUEUE: {QUEUE_NAME}")
except Exception as e:
    logger.exception("Failed to connect to Redis server.")

# ------------------------
# Task store
# ------------------------
task_results_store: Dict[str, Any] = {}

# ------------------------
# Pydantic Input Model
# ------------------------
class TestRequest(BaseModel):
    path: str
    selectedTests: list


@app.get("/ODI/check")
def check():
    logger.info("ODI Service Is Online..!")
    return {"message": "ODI Service Is Online..!"}

# ------------------------
# Background Task
# ------------------------
def _process_all_tests_in_background(task_id: str, original_input_json: dict):
    """
    Performs the heavy lifting of processing tests in the background.
    Updates the global task_results_store with status and results.
    """
    logger.info(f"Background task {task_id}: Starting processing.")

    # Create a deep copy to ensure modifications don't affect the original object
    processing_input_json = copy.deepcopy(original_input_json)
    try:
        # Update task status to "running"
        task_results_store[task_id] = {"status": "running", "progress": "Initializing"}

         # Search Page Mechanism
        relevant_pages = search_pages_mechanism(processing_input_json)

        logger.debug(f"Background task {task_id}: Relevant pages found: {relevant_pages}")
        task_results_store[task_id]["progress"] = "Pages searched"

        # Loop through each selected test to process
        for idx, test in enumerate(processing_input_json.get('selectedTests', [])):
            test_type = test.get('test_type')

            # Initialize test status and description
            test["test_status"] = False
            test["test_description"] = "Not processed or unsupported test type."
            task_results_store[task_id]["progress"] = f"Processing {test_type} ({idx+1}/{len(processing_input_json['selectedTests'])})"
            logger.debug(f"Processing {test_type} ({idx+1}/{len(processing_input_json['selectedTests'])})")

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

# ------------------------
# Routes
# ------------------------


@app.post("/ODI/initiate_file_processing")
def initiate_file_processing(request_data: TestRequest, background_tasks: BackgroundTasks):
    input_json = request_data.dict()
    logger.debug(f"Received input: {input_json}")

    if not os.path.exists(input_json.get("path", "")):
        logger.warning("Invalid file path provided.")
        raise HTTPException(status_code=400, detail="The provided path does not exist.")

    for test in input_json.get('selectedTests', []):
        if "normal_data" in test:
            if not test["normal_data"]:
                logger.error("normal_data exists but is empty or None.")
                raise HTTPException(status_code=400, detail="normal_data exists but value is invalid (None or empty dict)")

    task_id = str(uuid.uuid4())
    task_results_store[task_id] = {"status": "pending"}

    background_tasks.add_task(_process_all_tests_in_background, task_id, input_json)

    return JSONResponse(status_code=202, content={
        "status": True,
        "message": "File processing started in the background.",
        "task_id": task_id
    })

