import fitz  # PyMuPDF
from img2table.document import PDF
from img2table.ocr import TesseractOCR
import pandas as pd
import numpy as np
from io import BytesIO
import json
from flask import Flask, request, jsonify
from func import trt_main_function
from func import winding_resistance

app = Flask(__name__)

def validate_pdf(file):
    if file.filename == '':
        return False, 'No file selected'
    elif not file.filename.endswith('.pdf'):
        return False, 'Invalid file format. Only PDF files are allowed'
    else:
        return True, 'File read successfully'

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'message': 'No files'}), 400
    
    uploaded_file = request.files['pdf']
    
    # Validate the PDF file
    is_valid, message = validate_pdf(uploaded_file)
    if not is_valid:
        return jsonify({'Status': False, 'message': message}), 400
    

    # # Save the uploaded file to a temporary location
    file_path = "Pictures" + uploaded_file.filename
    uploaded_file.save(file_path)
    
    asset_name='s'   
    # Process the PDF and get the JSON result
    result_json = trt_main_function(file_path, asset_name)

    result_winding=winding_resistance(file_path, asset_name)
    return jsonify({'result_json': result_json, 'result_winding': result_winding})

    

if __name__ == '__main__':
    app.run(debug=True)
