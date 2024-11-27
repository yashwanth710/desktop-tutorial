import os
import threading
from redis_client import RedisClient;
# import uuid
import json

from flask import request
from flask import Flask, jsonify
from flask import Flask
from pdf_scraper import extract_test_result_json, extract_empty_result_json
import re 

app = Flask(__name__)

# pdf test results
# pdf_tests_data = {}
# fetch_pdf_data = threading.Lock() 

# Variable to store pdf training tasks
# pdf_processing_tasks = {}

import json

# Load configuration from a JSON file
with open('config.json') as f:
    config = json.load(f)
    
# temp file to save queues
file_path = 'redis_queue.txt'
write_redis = RedisClient(config["redis_ip"],config["redis_port"])

################ API developement

@app.route("/pdf/check")
def check_pdf():
    # app.logger.info("Hello, welcome to vfd")
    print("Inside vfd", flush=True)
    return {"message": "PDF Checked Successfully"}


"""
1. Initiate_pdf_processing
        test_output_json=Extract_test_result_json(input_json['selected],pdf_path)
        result_json=Test_level_json_creation(input_json,Output_json)
"""
@app.route('/pdf/intiate_pdf_processing', methods=['POST'])
def intiate_pdf_processing():
    # try:
    """
    Validate inputs from JSON.
    """
    input_json= request.get_json()
    pdf_path = input_json["path"]
    filename= os.path.basename(pdf_path)

    if not os.path.exists(pdf_path):
        return jsonify({"error": "The provided path does not exist.", "status": False}), 400

    if input_json["report_type"]=="Routine":
        print("intiating pdf_processing")
        """
        Intitate the processing of pdf and return unique_id
        """
        # Generate a unique id for this task
        # unique_id = str(uuid.uuid4())
        # Using threading to perform pdf_processing training in the background
        def pdf_processing():
            queue_name = config['queue_name']  # Get queue name from config
            try:
                # Save the unique id and status in the tasks dictionary
                # pdf_processing_tasks[unique_id] = {"status": "processing"}
                # simulate pdf_processing task
                result_json = extract_test_result_json(input_json, pdf_path)
                print(result_json)
                # Updating the status in the pdf_processing_tasks dictionary on completion
                result_json["test_status"] = 0
                result_json["test_description"] = "completed"

                # Serialize to JSON string
                serialized_result = json.dumps(result_json)
                # Update the fetch_pdf_data dictionary
                # pdf_tests_data[unique_id] = result_json
                # Send the data to the redis queue
                try:
                    write_redis.rpush(queue_name,serialized_result)
                    # read_queue_to_file(write_redis,queue_name,file_path)
                    # As data is already published clear the data from the queue
                    # pdf_tests_data.pop(unique_id, None)
                    # pdf_processing_tasks.pop(unique_id, None)
                except Exception as e:
                    print(e)
                
            except Exception as e:
                # print(e)
                e = str(e)
                pattern = 'Error code: 429'
                matched = re.findall(pattern, e)
                if len(matched) == 1:
                    # pdf_processing_tasks[unique_id]["status"] = "GPT error"
                    result_json = extract_empty_result_json(input_json, pdf_path,"The pdf file was unable to process exited due to GPT error"+e)
                else:                
                    # pdf_processing_tasks[unique_id]["status"] = "failed"
                    result_json = extract_empty_result_json(input_json, pdf_path,"Unable to process pdf file"+e)
                serialized_result = result_json    
                try:
                    write_redis.rpush(queue_name,json.dumps(serialized_result))
                    # As data is already published clear the data from the queue
                except Exception as e:
                    print(e)

        # Start the background pdf processing
        thread = threading.Thread(target=pdf_processing)
        thread.start()
        # Return a message with the unique id indicating that pdf_processing is running
        return jsonify({"message": f"{filename} is processing...", "test_status": 1})

    else:
        return jsonify({"message": "The provided report type is not supported for processing.", "status":False}), 400    

    # except Exception as e:
    #     return jsonify({"message": f"Failed to initiate pdf_processing {filename} file", "status": False}), 400

def read_queue_to_file(redis_client, queue_name, file_path):
    with open(file_path, 'w') as f:
        while True:
            # Read item from the queue
            item = redis_client.lpop(queue_name)
            print("queue..........",item)
            if item:
                f.write(item + '\n')
            else:
                break  # Exit if the queue is empty


"""
2.fetch_processed_pdf
"""
@app.route('/pdf/fetch_processed_pdf/<task_id>', methods=['GET'])
def fetch_processed_pdf(task_id):
    # Check if the unique_id is present in the pdf_processing_tasks dictionary
    # If present check its status
    if task_id in pdf_processing_tasks:
        status = pdf_processing_tasks[task_id]["status"]
        if status == "processing":
            # If the status is running, return a message indicating that forecasting is in progress
            return jsonify({"message": "PDF processing Is In Progress", "status": status})
        elif status == "completed":
            # Acquire the lock to ensure safe access to forecast_data
            with fetch_pdf_data:
                test_results = pdf_tests_data.pop(task_id, None)
                pdf_processing_tasks.pop(task_id, None)
                print(test_results)
            # If the status is completed, return the forecasted data
            if test_results:
                return jsonify({"message": "PDF Tests results available", "tests_data": test_results, "status": status})
            else:
                return jsonify({"message": "PDF Tests results not found", "status": status})
        elif status == 'failed':
            pdf_processing_tasks.pop(task_id, None)
            return jsonify({"message": "PDF processing failed",  "status": status})
        elif status == "GPT error":
            pdf_processing_tasks.pop(task_id, None)
            return jsonify({"message": "You exceeded your current quota, please check your plan and billing details",  "status": status})
    else: 
        return jsonify({"message": "Invalid unique id", "status": False}), 404

###fofof
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)