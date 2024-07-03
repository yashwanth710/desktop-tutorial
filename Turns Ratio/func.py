import fitz
from img2table.document import PDF
from img2table.ocr import TesseractOCR
import pandas as pd
from fuzzywuzzy import fuzz
import pdfplumber
import numpy as np
import json
import re
from datetime import datetime

####    TURNS RATIO Test
###### Main Function

def trt_main_function(file_path, asset_name):
    pdf_table_trt = turns_ratio_extract(file_path)
    trt_json = preprocess_data_trt(pdf_table_trt)
    return trt_json


##### Extracting

def turns_ratio_extract(file_path):
    # Open the PDF document
    pdf_document = fitz.open(file_path)
    target_phrases_trt = ['Turns Ratio test:','urns ratio test:']

    # Initialize a list to store page numbers and matched phrases
    pages_with_phrase_trt = []
    phrase_used_trt = []

    # Iterate through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_text = page.get_text("text").lower()

        # Iterate through each target phrase
        for phrase in target_phrases_trt:
            if phrase.lower() in page_text:
                # Append the page number and the matched phrase to the list
                pages_with_phrase_trt.append(page_number)
                phrase_used_trt.append(phrase)
        #Taking unique pages
        unique_page = set(pages_with_phrase_trt)
        pages_with_phrase_trt = list(unique_page)
    pdf = PDF(src=file_path, pages=pages_with_phrase_trt)
    ocr = TesseractOCR(lang="eng")

    # Table identification and extraction using tesseract ocr
    pdf_tables_trt = pdf.extract_tables(ocr=ocr)
    return pdf_tables_trt


### Preprocessing method-1

def preprocess_method_1(pdf_table_trt):    
    for key, tables in pdf_table_trt.items():
        df = tables[1].df  # Assuming the DataFrame is always at index 1
        
        # Find the index of the header row
        header_row_index = df[df.iloc[:, 0].str.startswith('Tap')].index[0]
        
        # Identify and drop columns containing '%DEVIATION', 'Error In %', or 'Ratio Error(%)'
        deviation_column_indices = [i for i, col in enumerate(df.iloc[header_row_index]) if '%DEVIATION' in col or 'Error In %' in col or 'Ratio Error(%)' in col]
        df = df.drop(columns=df.columns[deviation_column_indices])
        
        # Replace 'None' with NaN and forward fill
        df.replace('None', np.nan, inplace=True)
        df = df.ffill()
        
        # Set the header row
        df.columns = df.iloc[header_row_index]
        df = df[(header_row_index + 1):]
        
        # Drop rows where 'Calculated Ratio' is None
        df = df.dropna()
        
        # Clean up the first row
        df.iloc[0] = df.iloc[0].replace('\n', ' ', regex=True)
        df.iloc[0] = df.iloc[0].replace('\u2013', '-', regex=True)
        
        # Set the column headers
        cl = df.iloc[0]
        y3 = df[1:]
        y3.columns = cl
        y3.reset_index(drop=True, inplace=True)
        
        # Drop rows after 'Reverse' keyword
        reverse_start_index = y3[y3.apply(lambda row: row.astype(str).str.contains('Reverse').any(), axis=1)].index
        if not reverse_start_index.empty:
            y3 = y3.loc[:reverse_start_index[0]-1]
        
        # Convert the DataFrame to JSON format
        data = y3.to_dict('records')
        return data
    
#### Method-2

def preprocess_method_2(pdf_table_trt):
    
    for key, tables in pdf_table_trt.items():
        df = tables[0].df
        
        # Drop the first 6 rows and keep the first 6 columns
        df = df.drop(index=df.index[:6]).iloc[:, :6]
        
        # Drop the first column
        df = df.drop(df.columns[0], axis=1)
        
        # Identify and drop rows after "REVERSE ORDER"
        reverse_start_index = df[df.apply(lambda row: row.astype(str).str.contains('REVERSE ORDER').any(), axis=1)].index
        if not reverse_start_index.empty:
            df = df.loc[:reverse_start_index[0]-1]
        
        # Clean up the first row
        df.iloc[0] = df.iloc[0].replace('\n', ' ', regex=True)
        df.iloc[0] = df.iloc[0].replace('\u2013', '-', regex=True)
        
        # Set the column headers
        cl = df.iloc[0]
        y3 = df[1:]
        y3.columns = cl
        y3.reset_index(drop=True, inplace=True)
        
        # Convert the DataFrame to JSON format
        data = y3.to_dict('records')        
        return data
def preprocess_data_trt(pdf_table_trt):
    preprocessing_functions = [preprocess_method_1, preprocess_method_2]
    for preprocess in preprocessing_functions:
         try:
            # Attempt to preprocess the data using the current method
            preprocessed_data = preprocess(pdf_table_trt)
            return preprocessed_data
         except:
            ValueError
            # If the current method fails, print an error message and try the next method
            #print(f"Preprocessing with {preprocess.__name__} failed: {e}")
#     raise ValueError("Data format is not suitable for any predefined preprocessing methods")

#-------------------------------------------------------------------------------------------------

#######3 Winding Resistance

def winding_resistance(file_path, asset_name):
    pdf_tables, pages_with_phrase, phrase_used, HV_page, LV_page = table_extraction(file_path)
    HV,LV = table_format(pdf_tables, pages_with_phrase, HV_page, LV_page)
    HV,LV,Oil_Temperature,Reference_Temperature = final_winding(HV, LV, phrase_used, HV_page, LV_page, pdf_tables)
    return HV.to_dict('records'), LV.to_dict('records'), Oil_Temperature, Reference_Temperature

########### Extraction

def table_extraction(file_path):
    pdf_document = fitz.open(file_path)

    # Define the target phrases
    target_phrases = ['HV Side Winding Resistance', 'LV Side Winding Resistance', 'HV TO N', 'LV Winding Resistance']

    # Initialize a list to store page numbers and matched phrases
    pages_with_phrase = []
    phrase_used = []

    # Iterate through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_text = page.get_text("text").lower()

        # Iterate through each target phrase
        for phrase in target_phrases:
            if phrase.lower() in page_text:
                # Append the page number and the matched phrase to the list
                pages_with_phrase.append(page_number)
                phrase_used.append(phrase)
#         #Taking unique pages        
        unique_page = set(pages_with_phrase)
        pages_with_phrase = list(unique_page)

    if len(pages_with_phrase) == 2:
        HV_page = pages_with_phrase[0]
        LV_page = pages_with_phrase[1]
    elif len(pages_with_phrase) == 1:
#        HV_LV_page = pages_with_phrase[0]
        HV_page = pages_with_phrase[0]
        LV_page = pages_with_phrase[0]
    pdf = PDF(src=file_path, pages= [HV_page, LV_page])

    ocr = TesseractOCR(lang="eng")

    # Table identification and extraction using tesseract ocr
    pdf_tables = pdf.extract_tables(ocr=ocr)   
    return pdf_tables, pages_with_phrase, phrase_used, HV_page, LV_page

####### Format

def table_format(pdf_tables, pages_with_phrase, HV_page, LV_page):
    if len(pages_with_phrase) == 1:
        if len(pdf_tables[HV_page]) == 3 and len(pdf_tables[LV_page]) == 3:
            HV = pdf_tables[HV_page][1].df
            LV = pdf_tables[LV_page][2].df
        elif len(pdf_tables[LV_page]) == 5 and len(pdf_tables[HV_page]) == 5:
            HV = pdf_tables[HV_page][-2].df
            LV = pdf_tables[LV_page][-1].df
    elif len(pages_with_phrase) == 2:
        if len(pdf_tables[HV_page]) == 5 and len(pdf_tables[LV_page]) == 3:
            HV = pdf_tables[HV_page][-1].df
            LV = pdf_tables[LV_page][-1].df
        elif len(pdf_tables[HV_page]) == 1 and len(pdf_tables[LV_page]) == 3:
            HV = pdf_tables[HV_page][0].df
            LV = pdf_tables[LV_page][-1].df        
    return HV,LV

# Final

def final_winding(HV, LV, phrase_used, HV_page, LV_page, pdf_tables):
    if phrase_used == ['HV TO N', 'LV Winding Resistance']:
        HV.columns = HV.iloc[0]
        HV = HV[1:]
        LV.columns = LV.iloc[0]
        LV = LV[1:]
    elif phrase_used == ['HV Side Winding Resistance','LV Side Winding Resistance']:
        if len(pdf_tables[HV_page]) == 1 and len(pdf_tables[LV_page]) == 3:
            HV.columns = HV.iloc[5]
            Oil_Temperature = HV.iloc[6,2]
            Reference_Temperature = HV.iloc[6,3]
            Oil_Temperature = int(re.findall(r'\d+', Oil_Temperature)[0])
            Reference_Temperature = int(re.findall(r'\d+', Reference_Temperature)[0])
            HV = HV[7:]
            HV.reset_index(inplace = True, drop = True)
            reverse_start_index = HV[HV.apply(lambda row: row.astype(str).str.contains('REVERSE ORDER').any(), axis=1)].index[0]
            HV = HV[:21]
            HV = HV.dropna(axis = 1)
            col_1 = HV.columns[1]
            col_2 = HV.columns[2]
            col_1 = re.findall('1[A-Za-z] – 1N\\n\(Ω\)', col_1)[0]
            col_2 = re.findall('1[A-Za-z] – 1N\\n\(Ω\)', col_2)[0]
            HV.rename(columns = {HV.columns[0] : 'Tap No',HV.columns[1] : col_1, HV.columns[2] : col_2}, inplace = True)
            LV.columns = LV.loc[0]
            LV = LV.drop([0,1])
            LV.reset_index(drop = True, inplace = True)
        else:         
            Oil_Temperature = HV.iloc[1, 1]
            Oil_Temperature = int(re.findall(r'\d+', Oil_Temperature)[0])
            Reference_Temperature = HV.iloc[1,2]
            Reference_Temperature = int(re.findall(r'\d+', Reference_Temperature)[0])
            try:
                reverse_index = HV[HV[1] == 'Reverse'].index.tolist()[0]
                HV = HV.iloc[:reverse_index]
            except:
                IndexError
            HV.columns = HV.iloc[0]
            HV = HV[2:]
            HV.reset_index(drop = True, inplace = True)
            HV.columns = HV.columns.str.replace('\n', '')
            LV.columns = LV.iloc[0]
            LV = LV[2:]
            LV.reset_index(drop = True, inplace = True)
            LV.columns = LV.columns.str.replace('\n', '')
    
    return HV,LV,Oil_Temperature,Reference_Temperature

# #----------------------------------------------------------------------------------------------
# ####3 Oil Testing
# ## Main
# def RLA(file_path, excel_path,asset_name):
#     excel_1 = pd.read_excel(excel_path, sheet_name = 'DGA')
#     excel_2 = pd.read_excel(excel_path, sheet_name = 'MasterData')
#     pdf_tables_oil,pages_with_phrase_oil = table_extraction_oil(file_path)
#     table_oil = table_format_oil(pdf_tables_oil,pages_with_phrase_oil)
#     sample_date_oil, test_date_oil = extract_inf_date_oil(table_oil, file_path, pages_with_phrase_oil)
#     final_table_oil = template_creation_oil(table_oil, sample_date_oil, test_date_oil , excel_1)
#     return final_table_oil.to_dict('records')

# ### Extraction
# def table_extraction_oil(file_path):
#     pdf_document = fitz.open(file_path)
#     target_phrases_oil = ['On Line Test data','Test Data:  On-line test ']

#     # Initialize a list to store page numbers and matched phrases
#     pages_with_phrase_oil = []
#     phrase_used_oil = []

#     # Iterate through each page in the PDF
#     for page_number in range(pdf_document.page_count):
#         page = pdf_document[page_number]
#         page_text = page.get_text("text").lower()

#         # Iterate through each target phrase
#         for phrase in target_phrases_oil:
#             if phrase.lower() in page_text:
#                 # Append the page number and the matched phrase to the list
#                 pages_with_phrase_oil.append(page_number)
#                 phrase_used_oil.append(phrase)
#     pdf = PDF(src=file_path, pages=[pages_with_phrase_oil[0]])
#     ocr = TesseractOCR(lang="eng")

#     # Table identification and extraction using tesseract ocr
#     pdf_tables_oil = pdf.extract_tables(ocr=ocr)
#     return pdf_tables_oil,pages_with_phrase_oil

# ## Format
# def table_format_oil(pdf_tables_oil,pages_with_phrase_oil):
#     if len(pdf_tables_oil[pages_with_phrase_oil[0]])==1:
#         # extracting specific table
#         table_oil =pdf_tables_oil[pages_with_phrase_oil[0]][0].df
#         # cleaning data            
#         table_oil = table_oil[5:]

#     elif len(pdf_tables_oil[pages_with_phrase_oil[0]])==2:
#         # extracting specific table
#         table_oil =pdf_tables_oil[pages_with_phrase_oil[0]][1].df
    
#     return table_oil

# # INfo
# def extract_inf_date_oil(table_oil, file_path, pages_with_phrase_oil):
#     with pdfplumber.open(file_path) as pdf:
#         inf_json={}
#         page = pdf.pages[pages_with_phrase_oil[0]]
#         text = page.extract_text()
#         all_dates = re.findall(r'\b\d{2}[.\-\\]\d{2}[.\-\\]\d{2}(?:\d{2})?\b', text)
#         all_dates = [re.sub(r'[.\-\\]', '-', date) for date in all_dates]
#         if len(all_dates) == 2:
#             sample_date_oil = all_dates[0]
#             test_date_oil = all_dates[1]

#         elif len(all_dates) == 1:
#             sample_date_oil = all_dates[0]
#             test_date_oil = all_dates[0]

#     for fmt in ('%d-%m-%Y', '%d-%m-%y'):
#         try:
#             date_obj = datetime.strptime(sample_date_oil, fmt)
#         except ValueError:
#             continue
#     for fmt in ('%d-%m-%Y', '%d-%m-%y'):
#         try:
#             date_obj_1 = datetime.strptime(test_date_oil, fmt)
#         except ValueError:
#             continue

#     date_obj_1 = date_obj_1.replace(hour=1, minute=0, second=0)
#     sample_date_oil = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#     test_date_oil = date_obj_1.strftime('%Y-%m-%d %H:%M:%S')
#     inf_json['sample_date'] = sample_date_oil
#     inf_json["test_date"] = test_date_oil
#     return sample_date_oil, test_date_oil

# ## Template
# def template_creation_oil(table_oil, sample_date_oil, test_date_oil , excel_1):
#     table_oil.columns = table_oil.iloc[0]
#     table_oil = table_oil[2:]
#     table_oil = table_oil.T.drop_duplicates().T
#     cols = ['Test Description','Test Method','Result']
#     table_oil = table_oil[cols]
#     table_oil['Test Method'].ffill(inplace = True)
#     new_column_names = {'Test Description': 'DISPLAYNAME', 'Test Method': 'TESTMETHOD', 'Result': 'VALUETEXT'}
#     table_oil.rename(columns=new_column_names, inplace=True)
#     table_oil['DISPLAYNAME'] = table_oil['DISPLAYNAME'].apply(replace_str)

#     excel_1.drop(['VALUETEXT','TESTMETHOD'], axis = 'columns', inplace = True)
#     table_oil = pd.merge(excel_1, table_oil, on=['DISPLAYNAME'], how='left')
#     cols = ['SNO','ASSETNAME','TAGNAME','DISPLAYNAME', 'UOM','VALUETEXT', 'TESTMETHOD','SUBSYSTEM','TESTTYPE','SAMPLEDATE',
#             'TESTINGDATE', 'SAMPLEDBY', 'POSITION','POSITION(OTHER)','TESTEDBY','SAMPLINGMETHOD','REASONOFSAMPLING',
#             'ATMOSPHERICCONDITION']
#     table_oil = table_oil[cols]

#     table_oil['TESTTYPE'] = "Routine Test"
#     table_oil['SAMPLEDBY'] = 'Laxmi Associates'
#     table_oil['TESTEDBY'] = 'Laxmi Associates'
#     table_oil['SAMPLEDATE'] = sample_date_oil
#     table_oil['TESTINGDATE'] = test_date_oil
#     table_oil['VALUETEXT'] = table_oil['VALUETEXT'].str.replace('^', '**')
#     table_oil['VALUETEXT'] = table_oil['VALUETEXT'].replace({'NIL': 0, 'BDL': 0, 'N/d' : 0, 'N/D' : 0,'Nil' : 0})
#     table_oil['VALUETEXT'] = table_oil['VALUETEXT'].fillna(0)
#     table_oil['VALUETEXT'] = table_oil['VALUETEXT'].astype(str)
#     table_oil = table_oil.fillna('')

    
# #     table_oil['SAMPLEDATE'] = pd.to_datetime(table_oil['SAMPLEDATE'])
# #     table_oil['TESTINGDATE'] = pd.to_datetime(table_oil['TESTINGDATE'])
#     oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 90°C")
#     try:

#         table_oil.loc[oil_resistivity_mask, "VALUETEXT"]= eval(table_oil.loc[oil_resistivity_mask, "VALUETEXT"].iloc[0])
#     except: ValueError

#     try:

#         matches = re.match(r'^([\d.]+)\s+[xX]\s+\d+', table_oil.loc[oil_resistivity_mask, "VALUETEXT"].iloc[0])
#         table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = float(matches.group(1)) * (10 ** 12)
#     except:
#         pass
#     return table_oil

# ## Replace
# def replace_str(input_string):
#     input_string = input_string.replace('\n', '')
#     patterns_dict = {
#             r'Breakdown.*': 'Oil Breakdown Voltage',
#              r'Flash.*': 'Flash Point',
#              r'Water.*': 'Moisture OFF',
#              r'Inter.*': 'Inter Facial Tension',
#              r'Total Acid.*': 'Total Acid Number',
#              r'Sludge': 'Oil Sludge & Sediment',
#              r".*Specific.*90°[cC]$" : 'Oil Resistivity at 90°C',
#              r".*Dissipation.*@90°[cC]$": 'Dielectric Dissipation Factor at 90°C',
#              'Furan Analysis': 'Furan Analysis',
#              '5-hydroxy-methyl-2-furfuraldehyde': '5-Hydroxymethyl-2-feruldehyde',
#              '2-furfural': '2-Furaldehyde',
#              '2-Acetyl furan': '2-Acetylfuran',
#              '5-methyl-2-furaldehyde': '5-Methyl-2-furaldehyde',
#              '2-furfuryl alcohol': '2-Furfuryl alcohol',
#              'Total Furan': 'Total Furans',
#              'Dissolved Gas Analysis': 'Dissolved Gas Analysis',
#              'Hydrogen H2': 'H2 OFF',
#              'Methane CH4': 'CH4 OFF',
#              'Ethane C2H6': 'C2H6 OFF',
#              'Ethylene C2H4': 'C2H4 OFF',
#              'Acetelyne C2H2': 'C2H2 OFF',
#              'Carbon Monoxide CO': 'CO OFF',
#              'Carbon Di Oxide CO2': 'CO2 OFF',
#              'Nitrogen N2': 'N2 OFF',
#              'Oxygen O2': 'O2 OFF'
#                     }

#     for pattern, rep_str in patterns_dict.items():
#         if re.match(pattern, input_string): 
#             return re.sub(pattern, rep_str, input_string)
# #-----------------------------------------------------------------------------------------------------

# ##### MPS

# def MPS( excel_file_path,file_path,input_json):
#     # Reading DGA excel template
#     excel_sheet1 = pd.read_excel(excel_file_path, sheet_name = 'DGA')
#     excel_sheet2 = pd.read_excel(excel_file_path, sheet_name = 'MasterData')
    
#     # Extracting the table from pdf
#     raw_data = table_extraction(file_path)
    
#     # Processing the extracted table
#     preprocessed_data = main_preprocessing(data = raw_data)
    
#     # Extracting Information from pdf file outside of table
#     data_json = extracting_information(file_path,input_json["asset_name"])
    
#     # Creating a excel template for processed table
#     final_table = template_creation(preprocessed_data, data_json, excel_sheet1)    
    
#     # saving excel file
    
#     return final_table

# #### TABLE EXTRACTION

# # All the following functions are used as utility functions for data extraction, processing and template creation.
# def table_extraction(file_path):
#     """ This function is used to extract tables from pdf file"""
#     tables = []

#     with pdfplumber.open(file_path) as pdf:
#         for page_number in range(len(pdf.pages)):
#             page = pdf.pages[page_number]
#             table = page.extract_table()

#             # Append the table data to the list
#             if table:
#                 tables.append(table) 

#     table = pd.DataFrame(tables[0])
#     return table
    
# def concat_columns(row):
#     if row[1] == None:
#         return row['Test Parameter']
#     else:
#         return f"{row['Test Parameter']} {row[1]}"

# def concat_columns_1(row):
#     if row['Test Value'] == None:
#         return row['Limits (Max)']
#     else:
#         return row['Test Value']
    
# def concat_columns_2(row):
# #     print(row[1])
#     if row['Test Value'] == None:
#         return row['Limits']
#     else:
#         return row['Test Value']

# def replace_str(input_string):
#     """ This function is used to replace values in DISPLAYNAME column in template"""
#     input_string = input_string.replace('\n', '')
#     patterns_dict = {
#         r"Colo.*": "Oil Appearance",
#         r"Appe.*": "Oil Appearance",
#         r"Density.*": "Density at Temperature 20°C",
#         r"Breakdown.*" : "Oil Breakdown Voltage",
#         r"Water.*"  : "Moisture OFF",
#         r".*Resistivity.*@27°[cC]$" : "Oil Resistivity at 27°C",
#         r".*Resistivity.*@90°[cC]$" : "Oil Resistivity at 90°C",
#         r"Dielectric.*@27°[cC]$" : "Dielectric Dissipation Factor at 27°C",
#         r"Dielectric.*@90°[cC]$" : "Dielectric Dissipation Factor at 90°C",
#         r"Interfacial.*" : "Inter Facial Tension",
#         r"Flash.*" : "Flash Point",
#         r"Sediment.*" : "Oil Sludge & Sediment",
#         r"TGC.*" : "Total Gas Content OFF",
#         r"H2.*" : "H2 OFF",
#         r"O2.*" : "O2 OFF",
#         r"N2.*" : "N2 OFF",
#         r"CO.*monoxide.*" : "CO OFF",
#         r"CO2.*dioxide.*" : "CO2 OFF",
#         r"CH4.*" : "CH4 OFF",
#         r"C2H6.*" : "C2H6 OFF",
#         r"C2H4.*" : "C2H4 OFF",
#         r"C2H2.*" : "C2H2 OFF",
#         r"TDCG.*Total Dissolve.*" : 'Total Combustible Gases OFF',
#         r"TDCG/TGC.*" : "TDCG/TGC OFF",
#         r"Neutralisation.*" : "Neutralization Value (Acidity)",
#         r"5-Hydro.*" : "5-Hydroxymethyl-2-furaldehyde",
#         r"2-Furfur.*" : "2-Furfuryl alcohol",
#         r"2-fural.*" : "2-Furaldehyde",
#         r"2-Acetyl.*" : "2-Acetylfuran",
#         r"5-Methyl.*" : "5-Methyl-2-furaldehyde",
#         r"Total.*" : "Total Furans",
#         r"Estimated.*": "Estimated DP Value"

#     }

#     for pattern, rep_str in patterns_dict.items():
#         if re.match(pattern, input_string): 
#             return re.sub(pattern, rep_str, input_string)

# # Dictionary to replace oil appearance color naming
# oil_appereance_template={"yellowish brown":"Brown","light yellowish":"Pale Yellow",
#                          "reddish brown":"Dark Brown", "yellowish":"Yellow",
#                         "dark yellowish":"Brown"}

# def extracting_information(file_path, asset_name):
#     with pdfplumber.open(file_path) as pdf:
#         inf_json={}
#         for page in pdf.pages:
#             text = page.extract_text()

#             testing_date_match = re.search(r'Testing Date\s*:-\s*(\d+/\d+/\d+)', text)
#             test_certificate_match = re.search(r'Test Certificate No\.\s*:-\s*(\d+)', text)
#             sampling_date_match = re.search(r'Collected on\s*:-\s* (\d+/\d+/\d+)', text)
#             sampling_by = re.search(r'By\s*:-\s*(\w+)', text)
#             position_match = re.search(r'Position\s*:-\s*([\w-]+)', text)
#             sampling_method_match = re.search(r'Sampling\s*Method\s*\((.*?)\)', text)
#             ambient_humidity = re.search(r'Humidity\s*:-\s*([\w-]+)', text)
#             ambient_temperature = re.search(r'Temperature\s*:-\s*([\w-]+)', text)
#             print(ambient_humidity,ambient_temperature)
            
#             if sampling_method_match:
#                 sampling_method = sampling_method_match.group(1)
#                 sampling_method = sampling_method.strip()
#                 sampling_method = sampling_method.replace(' ','_')
#                 inf_json["sampling_method"]=sampling_method

#             if test_certificate_match:
#                 test_certificate_no = test_certificate_match.group(1)
#                 inf_json["test_certificate_no"]=test_certificate_no

#             if testing_date_match:
#                 test_date_str = testing_date_match.group(1)
#                 # Parsing date string to datetime object
#                 date_obj = datetime.strptime(test_date_str, '%d/%m/%Y')
#                 date_obj = date_obj.replace(hour=5, minute=30, second=0)

#                 # Converting datetime object to desired format
#                 test_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#                 inf_json["test_date"]=test_date

#             if sampling_date_match:
#                 sample_date_str = sampling_date_match.group(1)
#                 # Parsing date string to datetime object
#                 date_obj = datetime.strptime(sample_date_str, '%d/%m/%Y')
#                 date_obj = date_obj.replace(hour=5, minute=30, second=0)

#                 # Converting datetime object to desired format
#                 sample_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
#                 inf_json["sample_date"]=sample_date

#             if sampling_by:
#                 sampled_by = sampling_by.group(1)
#                 inf_json["sampled_by"]=sampled_by

#             if position_match:
#                 position = position_match.group(1)
#                 # Convert to lowercase for case-insensitive comparison
#                 position_lower = position.lower()
#                 if position_lower == "bottom":
#                     position = "Bottom"
#                 elif position_lower == "top":
#                     position = "Top"
#                 elif position_lower == "tank-1":
#                     position = "Top"
#                 inf_json["position"]=position
                
#             if ambient_humidity:
#                 ambient_humidity = ambient_humidity.group(1)
#                 inf_json["ambient_humidity"]=ambient_humidity
                
#             if ambient_temperature:
#                 ambient_temperature = ambient_temperature.group(1)
#                 inf_json["ambient_temperature"]=ambient_temperature
                
#             inf_json["asset_name"] =  asset_name  
#     return inf_json


# #### PRE-PROCESSING 

# def preprocess_method_1(data):
#     # Preprocess data using the first method

#     if len(data.columns) == 8:
#         data = data[1:]
#         data.columns = data.iloc[0]
#         data = data.iloc[1:-1]
#         data.loc[:,["Test Parameter","Test Method"]] = data.loc[:,["Test Parameter","Test Method"]].ffill()
#         x = data.iloc[:, :5]
#         y = data.iloc[:, 5:8]

#         x['Test Parameter'] = x.apply(concat_columns, axis=1)
#         new_column_names = {'Tested Gases': 'Test Parameter', 'Limits (Max)' : 'Limits'}
#         y.rename(columns = new_column_names, inplace = True)
#         y['Test Value'] = y.apply(concat_columns_2, axis=1)
#         x = x.drop(columns=[col for col in x.columns if col is None])
#         y = y.drop(columns=[col for col in y.columns if col is None])
# #         y.rename(columns = new_column_names, inplace = True)
#         data = pd.concat([x, y])

#     elif len(data.columns) == 5:
#         data=data[1:]
#         data.columns=data.iloc[0]
#         data=data.iloc[1:]
#         data=data[:-1]
#         data.loc[:,["Test Parameter","Test Method"]] = data.loc[:,["Test Parameter","Test Method"]].ffill()
#         data['Test Parameter'] = data.apply(concat_columns, axis=1)
#         data = data.drop(columns=[col for col in data.columns if col is None])
#         data.drop(data[data['Test Parameter'] == 'Appearance'].index, inplace=True)

#         data.dropna(subset = ['Test Parameter'], inplace = True)

# #    data.dropna(subset = ['Test Parameter'], inplace = True)
#     data['Test Method'] = data['Test Method'].str.replace(' ', '_')
#     new_column_names = {'Test Parameter': 'DISPLAYNAME', 'Test Method': 'TESTMETHOD', 'Test Value': 'VALUETEXT'}    
#     data.rename(columns = new_column_names, inplace = True)

#     data.reset_index(drop=True, inplace = True)    
#     contains_repeat = data['DISPLAYNAME'].str.contains('IInntteerrffaacciiaall').fillna(False)
#     data.loc[contains_repeat, ["DISPLAYNAME", 'TESTMETHOD', 'VALUETEXT']] = ['Interfacial Tension at 27 °C', 'IS 6104','NA']
#     data['DISPLAYNAME'] = data['DISPLAYNAME'].apply(replace_str)
#     contains_ohm = data['Limits'].str.contains('Ω-cm').fillna(False)
#     contains_gohm = data['Limits'].str.contains('GΩm').fillna(False)
#     contains_ohm_cm = data['Limits'].str.contains('ohm-cm').fillna(False)
#     contains_repeat = data['DISPLAYNAME'].str.contains('IInntteerrffaacciiaall').fillna(False)
#     if contains_ohm.any() == True and contains_gohm.any() == True:
#         data.loc[contains_ohm, "Test Value"] = pd.to_numeric(data.loc[contains_ohm, "Test Value"], errors="coerce")
#         data.loc[contains_gohm, "Test Value"] = pd.to_numeric(data.loc[contains_gohm, "Test Value"], errors="coerce")
#         data.loc[contains_ohm, 'VALUETEXT'] *= 10**12
#         data.loc[contains_gohm, 'VALUETEXT'] *= 10**11
#     else:
#         value_to_find = "Oil Resistivity at 27°C"  
#         value_to_find_1 = "Oil Resistivity at 90°C"
#         if contains_ohm_cm.any() == True:
#             data = data
#         else:
#             index = data[data['DISPLAYNAME'].str.contains(value_to_find, regex=False)].index
#             value = data.loc[index[0], 'VALUETEXT']
#             value = pd.to_numeric(value)
#             data.loc[index[0], 'VALUETEXT'] = value * 10**11
#             index_1 = data[data['DISPLAYNAME'].str.contains(value_to_find_1, regex=False)].index
#             value_1 = data.loc[index_1[0], 'VALUETEXT']
#             value_1 = pd.to_numeric(value_1)
#             data.loc[index_1[0], 'VALUETEXT'] = value_1 * 10**11
#     data = data.drop('Limits', axis = 1)
#     cols = ['DISPLAYNAME', 'VALUETEXT','TESTMETHOD' ]
#     data= data[cols] 
    
#     #calculating
#     preprocessed_data = data    
#     return preprocessed_data

# def preprocess_method_2(data):
#     # Preprocess data using the second method
#     data = data.drop([0,1], axis = 0)
#     data.columns = data.iloc[0]
#     data.drop(2, axis = 0, inplace = True)
#     data.loc[:,["Test Parameter","Test Method"]] = data.loc[:,["Test Parameter","Test Method"]].ffill()
#     data['Test Parameter'] = data.apply(concat_columns, axis=1)
#     data = data.drop(columns=[col for col in data.columns if col is None])
#     last_row = len(data) - 1
#     data = data.drop(data.index[last_row])
#     data=data.T.drop_duplicates().T
#     data_2 = data.iloc[:, [4,5,6]]
#     data = data.iloc[:, [0,1,2,3]]


#     new_column_names = {'Tested Gases': 'Test Parameter'}
#     data_2.rename(columns = new_column_names, inplace = True)
#     data = pd.concat([data, data_2])
#     data = data.dropna(subset=['Limits'])

#     contains_ohm = data['Limits'].str.contains('Ω-cm')
#     contains_gohm = data['Limits'].str.contains('GΩm')
#     # # Perform mathematical operation on values of 'Column2' where 'a' is present
#     # # For example, multiply by 2

#     data.loc[contains_ohm, "Test Value"] = pd.to_numeric(data.loc[contains_ohm, "Test Value"], errors="coerce")
#     data.loc[contains_gohm, "Test Value"] = pd.to_numeric(data.loc[contains_gohm, "Test Value"], errors="coerce")

#     data.loc[contains_ohm, 'Test Value'] *= 10**12
#     data.loc[contains_gohm, 'Test Value'] *= 10**11

#     data['Test Value'] = data.apply(concat_columns_2, axis=1)

#     data = data.drop('Limits', axis = 1)
#     data.drop(data[data['Test Parameter'] == 'Appearance'].index, inplace=True)
#     data.reset_index(drop=True, inplace = True)
#     data.dropna(subset = ['Test Parameter'], inplace = True)
#     data['Test Method'] = data['Test Method'].str.replace(' ', '_')
#     new_column_names = {'Test Parameter': 'DISPLAYNAME', 'Test Method': 'TESTMETHOD', 'Test Value': 'VALUETEXT'}
#     data.rename(columns = new_column_names, inplace = True)
#     cols = ['DISPLAYNAME', 'VALUETEXT','TESTMETHOD' ]
#     data= data[cols]
#     data['DISPLAYNAME'] = data['DISPLAYNAME'].apply(replace_str)
#     preprocessed_data = data

#     return preprocessed_data

# def preprocess_method_3(data):
#     # Preprocess data using the third method
#     data=data[1:]
#     data.columns=data.iloc[0]
#     data=data.iloc[1:]
#     data=data[:-1]
#     data.loc[:,["Test Parameter","Test Method"]] = data.loc[:,["Test Parameter","Test Method"]].ffill()
#     data['Test Parameter'] = data.apply(concat_columns, axis=1)
#     data = data.drop(columns=[col for col in data.columns if col is None])
#     data_3 = data.iloc[:,[7,8]]
#     data_2 = data.iloc[:, [4,5,6]]
#     data = data.iloc[:, [0,1,2,3]]
#     new_column_names = {'Test Parameter': 'DISPLAYNAME', 'Test Method': 'TESTMETHOD', 'Test Value': 'VALUETEXT','Tested Contents':'DISPLAYNAME', 'Test Value (ppb)':'VALUETEXT', 'Tested Gases':'DISPLAYNAME'}    
#     data.rename(columns = new_column_names, inplace = True)
#     data['DISPLAYNAME'] = data['DISPLAYNAME'].apply(replace_str)
#     contains_ohm = data['Limits'].str.contains('Ω-cm').fillna(False)
#     contains_gohm = data['Limits'].str.contains('GΩm').fillna(False)
#     contains_ohm_cm = data['Limits'].str.contains('ohm-cm').fillna(False)
#     if contains_ohm.any() == True and contains_gohm.any() == True:
#         data.loc[contains_ohm, "Test Value"] = pd.to_numeric(data.loc[contains_ohm, "Test Value"], errors="coerce")
#         data.loc[contains_gohm, "Test Value"] = pd.to_numeric(data.loc[contains_gohm, "Test Value"], errors="coerce")
#         data.loc[contains_ohm, 'VALUETEXT'] *= 10**12
#         data.loc[contains_gohm, 'VALUETEXT'] *= 10**11
#     else:
#         value_to_find = "Oil Resistivity at 27°C"
#         value_to_find_1 = "Oil Resistivity at 90°C"
#         if contains_ohm_cm.any() == True:
#             data = data
#         else:
#             index = data[data['DISPLAYNAME'].str.contains(value_to_find, regex=False)].index
#             value = data.loc[index[0], 'VALUETEXT']
#             value = pd.to_numeric(value)
#             data.loc[index[0], 'VALUETEXT'] = value * 10**11
#             index_1 = data[data['DISPLAYNAME'].str.contains(value_to_find_1, regex=False)].index
#             value_1 = data.loc[index_1[0], 'VALUETEXT']
#             value_1 = pd.to_numeric(value_1)
#             data.loc[index_1[0], 'VALUETEXT'] = value_1 * 10**11


#     data_2['Test Value'] = data_2.apply(concat_columns_2, axis=1)
#     data_2.rename(columns = new_column_names, inplace = True)
#     data_3.rename(columns = new_column_names, inplace = True)
#     data_2['DISPLAYNAME'] = data_2['DISPLAYNAME'].apply(replace_str)
#     data_3 = data_3.drop([9,10,11,12,13], axis = 0 )
#     data_3['DISPLAYNAME'] = data_3['DISPLAYNAME'].apply(replace_str)
#     data = pd.concat([data, data_2, data_3])
#     data = data.drop('Limits', axis = 1)
#     data.reset_index(drop=True, inplace = True)
#     data.dropna(subset = ['DISPLAYNAME'], inplace = True)
#     data['TESTMETHOD'] = data['TESTMETHOD'].str.replace(' ', '_')
#     cols = ['DISPLAYNAME', 'VALUETEXT','TESTMETHOD' ]
#     data= data[cols]
#     preprocessed_data = data
#     return preprocessed_data

# def preprocess_method_4(data):
    
#     if len(data.columns) == 9:
#         data = data[1:]
#         data.columns = data.iloc[0]
#         data = data.iloc[1:-1]

#         data.loc[:,["Test Parameter","Test Method"]] = data.loc[:,["Test Parameter","Test Method"]].ffill()
#         data['Test Parameter'] = data.apply(concat_columns, axis=1)
#         data = data.drop(columns=[col for col in data.columns if col is None])

#         x = data.iloc[:, :4]
#         y = data.iloc[:, 4:6]
#         z = data.iloc[:, 6:]

#         x.rename(columns={"Test Parameter": "DISPLAYNAME", "Test Method": "TESTMETHOD", "Test Value": "VALUETEXT"}, inplace=True)
#         y.rename(columns={"Tested Gases": "DISPLAYNAME", "Test Method": "TESTMETHOD", "Test Value": "VALUETEXT"}, inplace=True)
#         z.rename(columns={"Tested Contents": "DISPLAYNAME", "Test Method": "TESTMETHOD", "Test Value (ppb)": "VALUETEXT"}, inplace=True)

#         data = pd.concat([x, y, z], axis=0, ignore_index=True)
#         contains_ohm = data['Limits'].str.contains('Ω-cm').fillna(False)
#         contains_gohm = data['Limits'].str.contains('GΩm').fillna(False)

#         data.loc[contains_ohm, "VALUETEXT"] = pd.to_numeric(data.loc[contains_ohm, "VALUETEXT"], errors="coerce")
#         data.loc[contains_gohm, "VALUETEXT"] = pd.to_numeric(data.loc[contains_gohm, "VALUETEXT"], errors="coerce")

#         data.loc[contains_ohm, 'VALUETEXT'] *= 10**12
#         data.loc[contains_gohm, 'VALUETEXT'] *= 10**11
#         data = data.iloc[:31, :]
#         data.drop("Limits", axis=1, inplace=True)
#         column_order = ['DISPLAYNAME','VALUETEXT','TESTMETHOD']
#         data = data.reindex(columns=column_order)
#         data['TESTMETHOD'] = data['TESTMETHOD'].str.replace(' ', '_')
#         data['DISPLAYNAME'] = data['DISPLAYNAME'].apply(replace_str)

#         preprocessed_data = data
        
#     else:
#         pass
    
#     return preprocessed_data



# def main_preprocessing(data):
#     preprocessing_functions = [preprocess_method_1, preprocess_method_2, preprocess_method_3, preprocess_method_4]
#     for preprocess in preprocessing_functions:
#         try:
#             # Attempt to preprocess the data using the current method
#             preprocessed_data = preprocess(data)
#             print(f"Preprocessing successful with {preprocess.__name__}")
#             return preprocessed_data
#         except Exception as e:
#             # If the current method fails, print an error message and try the next method
#             print(f"Preprocessing with {preprocess.__name__} failed: {e}")
# #             print("Data format is not suitable for any predefined preprocessing methods")
#     raise ValueError("Data format is not suitable for any predefined preprocessing methods")

# #### TEMPLATE CREATION

# def template_creation(preprocessed_data, data_json, excel_sheet1):  
    
#     excel_sheet1.drop(['VALUETEXT','TESTMETHOD'], axis = 'columns', inplace = True)
#     # Merging preprocessed data to excel template
#     preprocessed_data = pd.merge(excel_sheet1, preprocessed_data, on=['DISPLAYNAME'], how='left')
    
#     # Changing oil appearance name
#     contains_Oil_Appearance	 = preprocessed_data['DISPLAYNAME'].str.contains('Oil Appearance')
#     preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'] = preprocessed_data['VALUETEXT'].str.replace('\n',' ')
#     index_value = preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'].index[0]
#     preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'] = preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'][index_value].lower()
#     words = preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'][index_value].split()
#     if words[-1] == 'color' or words[-1] == 'colour':
#         words.pop()
#         preprocessed_data.loc[contains_Oil_Appearance, 'VALUETEXT'] = ' '.join(words)
#     else:
#         pass
#     preprocessed_data['VALUETEXT'] = preprocessed_data['VALUETEXT'].replace(oil_appereance_template)
    
#     # Masking the data to replaces the values of the rows where the condition evaluates to True. 
#     contains_humidity = preprocessed_data['DISPLAYNAME'].str.contains('Ambient Humidity').fillna(False)
#     contains_temperature = preprocessed_data['DISPLAYNAME'].str.contains('Ambient Temperature').fillna(False)
#     # Adding ambient humidty and temperature data 
#     preprocessed_data.loc[contains_humidity, 'VALUETEXT'] = data_json['ambient_humidity']
#     preprocessed_data.loc[contains_temperature, 'VALUETEXT'] = data_json['ambient_temperature']
    
#     # Adding the data to template from data_json(from extracting information())
#     preprocessed_data["ASSETNAME"] = data_json["asset_name"]
#     preprocessed_data['SAMPLINGMETHOD']= data_json['sampling_method']
#     preprocessed_data['TESTINGDATE'] = data_json['test_date']
#     preprocessed_data['SAMPLEDATE'] = data_json['sample_date']
#     preprocessed_data['SAMPLEDBY'] = data_json['sampled_by']
#     preprocessed_data['POSITION'] = data_json['position']
#     preprocessed_data['POSITION(OTHER)'] = data_json['position']
#     preprocessed_data['TESTEDBY'] = data_json['sampled_by']
#     preprocessed_data['VALUETEXT'] = preprocessed_data['VALUETEXT'].replace({'NIL': 0, 'BDL': 0, 'N/d' : 0, 'ND' : 0, 'NA' : 0, 'Nil' : 0, '_' : 0})
#     preprocessed_data['TESTTYPE'] = "RoutineTest"
#     preprocessed_data['SAMPLEDATE'] = pd.to_datetime(preprocessed_data['SAMPLEDATE'])
#     preprocessed_data['TESTINGDATE'] = pd.to_datetime(preprocessed_data['TESTINGDATE'])
#     # Maintaing the template column order 
#     cols = ['SNO','ASSETNAME','TAGNAME','DISPLAYNAME', 'UOM','VALUETEXT', 'TESTMETHOD','SUBSYSTEM','TESTTYPE','SAMPLEDATE', 
#             'TESTINGDATE', 'SAMPLEDBY', 'POSITION','POSITION(OTHER)','TESTEDBY','SAMPLINGMETHOD','REASONOFSAMPLING',
#             'ATMOSPHERICCONDITION']
#     pdf_data = preprocessed_data[cols]
    
#     return pdf_data

# #----------------------------------------------------------------------------------

# # user_test_json = {
# #   "vendor_name": "laxmi associates",
# #   "asset_name": "hyh101",
# #   "selectedTests": {
# #     "Oil Testing": True,
# #     "Winding Resistance": True,
# #     "Turns Ratio Test": True
# #   }
# # }

# # user_test_json = {
# #   "vendor_name": "MPS",
# #   "asset_name": "hyh101",
# #   "selectedTests": {
# #     "Oil Testing": True
# #   }
# # }

# # selected_tests = []
# # test_jsons = []
# # test_pair = {}

# # if user_test_json['vendor_name'] == "laxmi associates":
# #     for i in user_test_json['selectedTests'].items():
        
# #         if True in (i):
# #             selected_tests.append(i[0])
# #             if 'Oil Testing' in selected_tests:
# #                 oil_testing = RLA(file_path, excel_path,asset_name)
# # #                test_jsons.append(oil_testing)
# #                 test_pair['Oil Testing'] = oil_testing

# #             if 'Winding Resistance' in selected_tests:
# #                 HV, LV, Oil_Temperature, Reference_Temperature = winding_resistance(file_path, asset_name)
# # #                test_jsons.append(winding_resistance_1)
# #                 temperature = {'Oil_Temperature' : Oil_Temperature,'Reference_Temperature' : Reference_Temperature}
# #                 test_pair['Winding Resistance'] = {}
# #                 test_pair['Winding Resistance']['Temperature'] = temperature
# #                 test_pair['Winding Resistance']['Tests'] = {}
# #                 test_pair['Winding Resistance']['Tests']['HV'] = HV
# #                 test_pair['Winding Resistance']['Tests']['LV'] = LV
    
# #             if 'Turns Ratio Test' in selected_tests:
# #                 turns_ratio = trt_main_function(file_path, asset_name)
# # #                test_jsons.append(turns_ratio)
# #                 test_pair['Turns Ratio Test'] = turns_ratio
    
# # elif user_test_json['vendor_name'] == 'MPS':
# #     oil_testing = MPS( excel_file_path,file_path,input_json)
# #     test_pair['Oil Testing'] = oil_testing
    
