import requests
import pandas as pd
from io import BytesIO
import os


url = 'http://127.0.0.1:8080/upload-pdf'
path=os.getcwd()
filepath=f"{path}\sample_pdf.pdf"
print(filepath)
files = {'pdf': open(filepath, 'rb')}  
data = {'json': '{"asset_name": "TR-01","vendor_name": "mps"}'}  

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    excel_file = BytesIO(response.content)
    df = pd.read_excel(excel_file)
    print(df.columns)
    print("Excel file read successfully")
else:
    print("Failed to read excel File. Status code:", response.status_code)