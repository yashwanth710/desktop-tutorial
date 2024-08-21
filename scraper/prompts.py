import re 
import pandas as pd 
import json

# test prompts
################################################
"""
relevant_page_level_dictionary
{
    "Oil Testing": "prompt",
    "Winding Resistance": "prompt",
    "Turns Ratio Test": "prompt",
    "insulation_test":"prompt"
    }


llm_model_prompts
{
    "Oil Testing": "prompt",
    "Winding Resistance": "prompt",
    "Turns Ratio Test": "prompt",
    "insulation_test":"prompt"
    }
"""

############################################


relevant_page_level_dictionary = {"Oil Testing" : """Analyze the following text and determine if it mentions any information related to oil properties, 
    DGA gases, or Furan values. Specifically, look for the presence of the following parameters: Appearance, 
    Density at 29.5 °C, Breakdown Voltage, Water Content, Neutralisation Value, Resistivity @27°C, Resistivity @90°C,
    Dielectric Disipation Factor @27°C, Dielectric Disipation Factor @90°C, Interfacial Tension, Flash Point, 
    Sediment & Sludge, TGC Total Gas Content %, Hydrogen (H2), Oxygen (O2), Nitrogen (N2), Carbon monoxide (CO), 
    Carbon dioxide (CO2), Methane (CH4), Ethane (C2H6), Ethylene (C2H4), Acetylene (C2H2), 
    Total Dissolved Combustible Gas (TDCG), TDCG/TGC ( %), 5-Hydroxymethyl-2-furuldehyde, 2-Furfurol (furfuryl alcohol),
    2-Furaldehyde, 2-Acetylfuran, 5-Methyl-2-furaldehyde, Total Furans, Estimated DP Value. 
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""" }


    
llm_model_prompts = {"Oil Testing" : """
    Extract the details of Oil tests, DGA, and Furans from the given text, if the values are not available leave it.
    Ensure to include all the Test Methods, Limits, and Test Values for each parameter.
    Also extract Ambient Humidity and Ambient Temperature from the text.
    Provide the output in JSON format as shown in the example below. :
    {
      {
        "Appearance": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Density": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Breakdown Voltage": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Water Content": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Neutralisation Value": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Resistivity @27°C": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Resistivity @90°C": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Dielectric Disipation Factor @27°C": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Dielectric Disipation Factor @90°C": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Interfacial Tension": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Flash Point": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Sediment & Sludge": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "TGC Total Gas Content %": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Hydrogen (H2)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Oxygen (O2)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Nitrogen (N2)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Carbon monoxide (CO)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Carbon dioxide (CO2)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Methane (CH4)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Ethane (C2H6)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Ethylene (C2H4)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Acetylene (C2H2)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Total Dissolved Combustible Gas (TDCG)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "TDCG/TGC (%)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "5-Hydroxymethyl-2-furuldehyde": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "2-Furfurol (furfuryl alcohol)": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "2-Furaldehyde": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "2-Acetylfuran": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "5-Methyl-2-furaldehyde": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Total Furans": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Estimated DP Value": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Temperature": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Humidity": {"TESTMETHOD": "", "LIMITS": "", "VALUETEXT": ""},
        "Metadata": {"POSITION": ""}
      }
    }
    Units are not required to extract.
    If Limits are not provided then you can leave them empty. 
    """}

########################### Convert and Evaluate ###########################

def convert_and_evaluate(expression):

    try:        
        # Replace the multiplication symbol ' x ' or 'X' with '*'
        expression = expression.replace(' x ', ' * ').replace('X', '*')

        # Replace '^' with '**' for exponentiation
        expression = expression.replace('^', '**')
        
        # Replace '10' followed by digits with '10**' followed by those digits
        expression = re.sub(r'10(\d+)', r'10**\1', expression)
        
        # Replace superscript numbers with regular numbers
        superscript_map = {
            '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
            '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
        }
        expression = re.sub(r'[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+', lambda x: ''.join(superscript_map.get(char, char) for char in x.group()), expression)
        expression = re.sub(r'(\d+)\*\*(\d+)', r'\1**\2', expression)  # Handle remaining superscript conversions
        
        # Evaluate the expression
        result = eval(expression)
        
        return result
    except Exception:
        return expression


############################# DGA Template creation ##########################

def DGA_template_creation(response):
    response = response[8:-4:]
    response = response.replace('\n', '')
    response = json.loads(response)

    # Table Creation 
    transformed_data = []
    for display_name, values in response.items():
        new_entry = {'DISPLAYNAME': display_name}
        new_entry.update(values)
        transformed_data.append(new_entry)
    final_data = pd.DataFrame(transformed_data)


    temp_df = pd.DataFrame(temp)
    final_data['DISPLAYNAME'].replace(name_replacements,inplace = True)
    #final_data['POSITION'].bfill(inplace = True)
    #final_data = final_data.iloc[:-1]
    table_oil = pd.merge(temp_df, final_data, on=['DISPLAYNAME'], how='left')
    contains_ohm = table_oil['LIMITS'].str.contains('Ω-cm').fillna(False)
    contains_gohm = table_oil['LIMITS'].str.contains('GΩm').fillna(False)
    #if contains_ohm.any() or contains_gohm.any() == True:
    try:
        oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 27°C")
        expression = table_oil.loc[oil_resistivity_mask, "VALUETEXT"][table_oil.loc[oil_resistivity_mask, "VALUETEXT"].index[0]]
        if len(str(expression)) > 1:    
            table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = convert_and_evaluate(expression)
        else:
            pass
        oil_resistivity_mask = (table_oil["DISPLAYNAME"] == "Oil Resistivity at 90°C")
        expression = table_oil.loc[oil_resistivity_mask, "VALUETEXT"][table_oil.loc[oil_resistivity_mask, "VALUETEXT"].index[0]]
        if len(str(expression)) > 1:
            table_oil.loc[oil_resistivity_mask, "VALUETEXT"] = convert_and_evaluate(expression)
    except ValueError:
        pass
        
    try:
        table_oil.loc[contains_ohm, "VALUETEXT"] = pd.to_numeric(table_oil.loc[contains_ohm, "VALUETEXT"], errors="coerce")
        table_oil.loc[contains_gohm, "VALUETEXT"] = pd.to_numeric(table_oil.loc[contains_gohm, "VALUETEXT"], errors="coerce")
        table_oil.loc[contains_ohm, 'VALUETEXT'] *= 10**12
        table_oil.loc[contains_gohm, 'VALUETEXT'] *= 10**11
    except ValueError:
        pass

    table_oil.drop('LIMITS', axis = 1, inplace = True)
    table_oil['VALUETEXT'] = table_oil['VALUETEXT'].replace({'NIL': 0, 'BDL': 0, 'N/d' : 0, 'N/D' : 0,'Nil' : 0, 'ND' : 0})
    contains_Oil_Appearance	 = table_oil['DISPLAYNAME'].str.contains('Oil Appearance')
    table_oil.loc[contains_Oil_Appearance, 'VALUETEXT'] = table_oil['VALUETEXT'].str.replace('\n',' ')
    table_oil.drop('POSITION', axis = 1, inplace = True)
    return table_oil

############################### Name Replacements ###########################

name_replacements = {
    'Appearance': 'Oil Appearance',
    'Density': 'Density at Temperature 20°C',
    'Breakdown Voltage': 'Oil Breakdown Voltage',
    'Water Content': 'Moisture OFF',
    'Neutralisation Value': 'Neutralization Value (Acidity)',
    'Resistivity @27°C': 'Oil Resistivity at 27°C',
    'Resistivity @90°C': 'Oil Resistivity at 90°C',
    'Dielectric Disipation Factor @27°C': 'Dielectric Dissipation Factor at 27°C',
    'Dielectric Disipation Factor @90°C': 'Dielectric Dissipation Factor at 90°C',
    'Interfacial Tension': 'Inter Facial Tension',
    'Flash Point': 'Flash Point',
    'Sediment & Sludge': 'Oil Sludge & Sediment',
    'TGC Total Gas Content %': 'Total Gas Content OFF',
    'Hydrogen (H2)': 'H2 OFF',
    'Oxygen (O2)': 'O2 OFF',
    'Nitrogen (N2)': 'N2 OFF',
    'Carbon monoxide (CO)': 'CO OFF',
    'Carbon dioxide (CO2)': 'CO2 OFF',
    'Methane (CH4)': 'CH4 OFF',
    'Ethane (C2H6)': 'C2H6 OFF',
    'Ethylene (C2H4)': 'C2H4 OFF',
    'Acetylene (C2H2)': 'C2H2 OFF',
    'Total Dissolved Combustible Gas (TDCG)': 'Total Combustible Gases OFF',
    'TDCG/TGC (%)': 'TDCG/TGC OFF',
    '5-Hydroxymethyl-2-furuldehyde': '5-Hydroxymethyl-2-furaldehyde',
    '2-Furfurol (furfuryl alcohol)': '2-Furfuryl alcohol',
    '2-Furaldehyde': '2-Furaldehyde',
    '2-Acetylfuran': '2-Acetylfuran',
    '5-Methyl-2-furaldehyde': '5-Methyl-2-furaldehyde',
    'Total Furans': 'Total Furans',
    'Estimated DP Value': 'Estimated DP Value',
    'Temperature': 'Ambient Temperature',
    'Propane + Propylene (C3H8+C3H6)': 'Propane+Propylene ( C3H6+C3H8) OFF',
    'Humidity': 'Ambient Humidity'
}


################################ Template ###############################

temp = {
 'TAGNAME': {0: 'MT_AMB_HUMIDITY_OIL_TEST_OFF',
  1: 'MT_AMB_TEMP_OIL_TEST_OFF',
  2: 'MT_OIL_C2H2_OFF',
  3: 'MT_OIL_C2H4_OFF',
  4: 'MT_OIL_C2H6_OFF',
  5: 'MT_OIL_C3H6_C3H8_OFF',
  6: 'MT_OIL_CH4_OFF',
  7: 'MT_OIL_CO2_OFF',
  8: 'MT_OIL_CO_OFF',
  9: 'MT_OIL_H2_OFF',
  10: 'MT_OIL_MST_OFF',
  11: 'MT_OIL_N2_OFF',
  12: 'MT_OIL_O2_OFF',
  13: 'MT_OIL_TCG_OFF',
  14: 'MT_OIL_TDCG_OFF',
  15: 'MT_OIL_TDCG_TGC_OFF',
  16: 'MT_OIL_TGC_OFF',
  17: 'OIL_TEMP_OFF',
  18: 'MT_CORR_SULPHUR_AT_TEMP_T1_FOR_TIME_T1_OFF',
  19: 'MT_OIL_BREAKDOWN_VOLT_OFF',
  20: 'MT_OIL_DENSITY_AT_TEMP_T2_OFF',
  21: 'MT_OIL_DIE_DF_AT_27_DEG_OFF',
  22: 'MT_OIL_DIE_DF_AT_90_DEG_OFF',
  23: 'MT_OIL_FLASH_POINT_OFF',
  24: 'MT_OIL_INTERFACIAL_TENS_OFF',
  25: 'MT_OIL_KINEMATIC_VISCOSITY_TEMP_T1_OFF',
  26: 'MT_OIL_KINEMATIC_VISCOSITY_TEMP_T2_OFF',
  27: 'MT_OIL_POUR_POINT_OFF',
  28: 'MT_OIL_RESITIVITY_AT_27_DEG_OFF',
  29: 'MT_OIL_RESITIVITY_AT_90_DEG_OFF',
  30: 'MT_OIL_TOTAL_ACID_NO',
  31: 'OIL_APPEARANCE',
  32: 'OIL_SLUDGE_SEDIMENT',
  33: 'MT_OIL_FUR_5_C6H6O2_OFF',
  34: 'MT_OIL_FUR_C5H4O2_OFF',
  35: 'MT_OIL_FUR_C5H6O2_OFF',
  36: 'MT_OIL_FUR_C6H6O2_OFF',
  37: 'MT_OIL_FUR_C6H6O3_OFF',
  38: 'MT_OIL_FUR_ESTMD_DP_VALUE_OFF',
  39: 'MT_OIL_FUR_TOTAL_FURAN_OFF'},
 'DISPLAYNAME': {0: 'Ambient Humidity',
  1: 'Ambient Temperature',
  2: 'C2H2 OFF',
  3: 'C2H4 OFF',
  4: 'C2H6 OFF',
  5: 'Propane+Propylene ( C3H6+C3H8) OFF',
  6: 'CH4 OFF',
  7: 'CO2 OFF',
  8: 'CO OFF',
  9: 'H2 OFF',
  10: 'Moisture OFF',
  11: 'N2 OFF',
  12: 'O2 OFF',
  13: 'Total Combustible Gases OFF',
  14: 'TDCG OFF',
  15: 'TDCG/TGC OFF',
  16: 'Total Gas Content OFF',
  17: 'Oil Temperature OFF',
  18: 'Corrosive Sulphur at 150°C for 72 hrs',
  19: 'Oil Breakdown Voltage',
  20: 'Density at Temperature 20°C',
  21: 'Dielectric Dissipation Factor at 27°C',
  22: 'Dielectric Dissipation Factor at 90°C',
  23: 'Flash Point',
  24: 'Inter Facial Tension',
  25: 'Kinematic Viscosity at 40°C',
  26: 'Kinematic Viscosity at 30°C',
  27: 'Pour Point',
  28: 'Oil Resistivity at 27°C',
  29: 'Oil Resistivity at 90°C',
  30: 'Neutralization Value (Acidity)',
  31: 'Oil Appearance',
  32: 'Oil Sludge & Sediment',
  33: '5-Methyl-2-furaldehyde',
  34: '2-Furaldehyde',
  35: '2-Furfuryl alcohol',
  36: '2-Acetylfuran',
  37: '5-Hydroxymethyl-2-feruldehyde',
  38: 'Estimated DP Value',
  39: 'Total Furans'}}