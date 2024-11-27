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


# relevant_page_level_dictionary = {"Oil Testing" : """Analyze the following text and determine if it mentions any information related to oil properties, 
#     DGA gases, or Furan values. Specifically, look for the presence of the following parameters: Appearance, 
#     Density at 29.5 °C, Breakdown Voltage, Water Content, Neutralisation Value, Resistivity @27°C, Resistivity @90°C,
#     Dielectric Disipation Factor @27°C, Dielectric Disipation Factor @90°C, Interfacial Tension, Flash Point, 
#     Sediment & Sludge, TGC Total Gas Content %, Hydrogen (H2), Oxygen (O2), Nitrogen (N2), Carbon monoxide (CO), 
#     Carbon dioxide (CO2), Methane (CH4), Ethane (C2H6), Ethylene (C2H4), Acetylene (C2H2), 
#     Total Dissolved Combustible Gas (TDCG), TDCG/TGC ( %), 5-Hydroxymethyl-2-furuldehyde, 2-Furfurol (furfuryl alcohol),
#     2-Furaldehyde, 2-Acetylfuran, 5-Methyl-2-furaldehyde, Total Furans, Estimated DP Value. 
#     If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""" }


    
# def llm_model_prompt_func(modified_llm_oil_json):

#     llm_model_prompts = {"Oil Testing" : f"""
#         Extract the details of Oil tests, DGA, and Furans from the given text, if the values are not available leave it.
#         Ensure to include all the Test Methods, Limits, and Test Values for each parameter.
#         Provide the output in JSON format as shown in the example below. :
        
#     {modified_llm_oil_json}
    
#         Units are not required to extract.
#         If Limits are not provided then you can leave them. 

#         Do not provide any other textual information apart from the JSON.
#         """}
    
#     return llm_model_prompts






relevant_page_level_dictionary = {
    "Turns Ratio Testing": """
    Analyze the following text to identify any information related to the Turns Ratio test.
    Specifically, search for the following parameters: Tap No, Measured Ratio, Calculated Ratio, 
    1U - 1N/2U - 2W, 1V - 1N/2U - 2V, 1W - 1N/2W - 2V, HV Side Voltage(KV), LV Side Voltage(KV).
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.
    """
}

def llm_model_prompt_func_turns_ratio(modified_llm_turns_ratio_json):

    llm_model_prompts = {
        "Turns Ratio Testing": f"""
            Extract all details of the Turns Ratio test from the given text, including each Tap No, 
            Measured Ratio, and Calculated Ratio. If values are missing, leave them empty. 
            Ensure to capture all instances for each parameter without duplicating or missing any entries.

            Format the output in JSON as shown in this example:

            {{
                'Tap No': '1',
                '1U - 1N/ 2U - 2W': '9.6512',
                '1V - 1N/ 2U - 2V': '9.6479',
                '1W - 1N/ 2W - 2V': '9.6524',
                'CALCULATED RATIO': '9.6600'
            }}

            Ignore values with any of the following terms: '%DEVIATION', 'Error In %', 'Ratio Error %', 
            'reverse', 'U-phase', 'V-phase', 'W-phase'. 

            Provide only the JSON structure as output, with no extra textual information.
        """
    }
    
    return llm_model_prompts
