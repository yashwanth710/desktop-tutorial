import os,re,json,threading
from dotenv import load_dotenv
from pdf_scraper import pdf_main
from redis_client import RedisClient;
from flask import Flask,request,jsonify

app = Flask(__name__)

# pdf test results
# pdf_tests_data = {}
# fetch_pdf_data = threading.Lock() 

# Variable to store pdf training tasks
# pdf_processing_tasks = {}


path=os.getcwd()

load_dotenv()
api_key=os.getenv("OPENAI_API_KEY")

# Load configuration from a JSON file
# with open('PDF_Scraper\src\config.json') as f:
with open('/app/src/config.json') as f:
    config = json.load(f)
    
# temp file to save queues
file_path = 'redis_queue.txt'
write_redis = RedisClient(config["redis_ip"],config["redis_port"])

################ API developement

@app.route("/pdf/check")
def check_pdf():
    # app.logger.info("Hello, welcome to vfd")
    print("Inside pdf", flush=True)
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

    pdf = pdf_main(pdf_path, input_json, api_key)

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
                result_json = pdf.extract_test_result_json()
                
                # Updating the status in the pdf_processing_tasks dictionary on completion
                result_json["test_status"] = 0
                result_json["test_description"] = "completed"
                print(result_json)
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
                    print('testttt')
                    print(e)
                    return jsonify({"Status": False, "message":f"failed to update data in Redis,{e}"})
                
            except Exception as e:
                # print(e)
                e = str(e)
                pattern = 'Error code: 429'
                matched = re.findall(pattern, e)
                if len(matched) == 1:
                    # pdf_processing_tasks[unique_id]["status"] = "GPT error"
                    result_json = pdf.extract_empty_result_json("The pdf file was unable to process exited due to GPT error"+e)
                else:                
                    # pdf_processing_tasks[unique_id]["status"] = "failed"
                    result_json = pdf.extract_empty_result_json("Unable to process pdf file"+e)
                serialized_result = result_json    
                try:
                    write_redis.rpush(queue_name,json.dumps(serialized_result))
                    # As data is already published clear the data from the queue
                except Exception as e:
                    print('testttt2')
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




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)