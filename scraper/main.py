import os
import threading

import uuid
from flask import request, Response
from flask import Flask, jsonify, make_response
from flask import Flask, render_template,url_for
from pdf_scraper import extract_test_result_json

app = Flask(__name__)

# pdf test results
pdf_tests_data = {}
fetch_pdf_data = threading.Lock() 

# Variable to store pdf training tasks
pdf_processing_tasks = {}


################ API developement
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
        unique_id = str(uuid.uuid4())
        # Using threading to perform pdf_processing training in the background
        def pdf_processing():
            try:
                # Save the unique id and status in the tasks dictionary
                pdf_processing_tasks[unique_id] = {"status": "processing"}
                # simulate pdf_processing task
                result_json = extract_test_result_json(input_json, pdf_path)
                # Updating the status in the pdf_processing_tasks dictionary on completion
                pdf_processing_tasks[unique_id]["status"] = "completed"
                # Update the fetch_pdf_data dictionary
                pdf_tests_data[unique_id] = result_json

            except Exception as e:
                pdf_processing_tasks[unique_id]["status"] = "failed"

        # Start the background pdf processing
        thread = threading.Thread(target=pdf_processing)
        thread.start()
        # Return a message with the unique id indicating that pdf_processing is running
        return jsonify({"message": f"{filename} processing is initiated...", "id": unique_id})

    else:
        return jsonify({"message": "The provided report type is not supported for processing.", "status":False}), 400    

    # except Exception as e:
    #     return jsonify({"message": f"Failed to initiate pdf_processing {filename} file", "status": False}), 400



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
    else:
        return jsonify({"message": "Invalid unique id", "status": False}), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)