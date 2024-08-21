{
    "llm_model_prompts": {
        "DGA": """
            Extract the details of Oil tests, DGA, and Furans from the given text, if the values are not available leave it.
            Ensure to include all the Test Methods, Limits, and Test Values for each parameter.
            Also extract Ambient Humidity and Ambient Temperature from the text.
            Provide the output in JSON format as shown in the example below:
            {
                "Appearance": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Density": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Breakdown Voltage": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Water Content": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Neutralisation Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Interfacial Tension": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Flash Point": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Sediment & Sludge": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TGC Total Gas Content %": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Hydrogen (H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Oxygen (O2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Nitrogen (N2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon monoxide (CO)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon dioxide (CO2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Methane (CH4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethane (C2H6)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethylene (C2H4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Acetylene (C2H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Dissolved Combustible Gas (TDCG)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TDCG/TGC ( %)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Hydroxymethyl-2-furuldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furfurol (furfuryl alcohol)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Acetylfuran": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Methyl-2-furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Furans": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Estimated DP Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Temperature": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Humidity": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Metadata": {
                    "POSITION": ""
                }
            }
            Units are not required to extract.
            If Limits are not provided then you can leave them.
        `,
        "Turns Ratio": `
            Find the Turns Ratio test table and only extract the information of Tap No, MEASURED RATIO, CALCULATED RATIO. Exclude the row from the reverse, u-phase, v-phase, w-phase, ratio error, deviation, error in.
            And provide the output in the json format completely as given in the example. Do not miss any of the Measured Ratio values. Refer to this example json format for response:
            {
                'Tap No.': '1',
                '1U - 1N/ 2U -2W': '9.6512',
                '1V - 1N/ 2U - 2V': '9.6479',
                '1W - 1N/ 2W - 2V': '9.6524',
                'CALCULATED RATIO': '9.6600'
            }
            If only 'Tap No' and 'CALCULATED RATIO' are present, provide the output in the following format:
            {
                'Tap No': '1',
                'CALCULATED RATIO': '9.54'
            }
        `,
        "Winding Resistance": `
            Retrieve the Winding Resistance test data, only extract tables for HV Side and LV Side. Do not extract data for Reverse Order Resistance.
            Provide the output in JSON format completely. Provide all the values from the table. Given below is the example for your reference.
            Do not miss any of the values from HV side and LV Side. Just provide me the json only:
            {
                "Oil Temperature": "40",
                "Reference Temperature": "75",
                "HV": [
                    {
                        "Tap No.": "1",
                        "1U - 1N(mΩ)": "371.5",
                        "1V - 1N(mΩ)": "369.5",
                        "1W - 1N(mΩ)": "369.9"
                    },
                    {
                        "Tap No.": "2",
                        "1U - 1N(mΩ)": "361.2",
                        "1V - 1N(mΩ)": "359.5",
                        "1W - 1N(mΩ)": "362.5"
                    }
                ],
                "LV": [
                    {
                        "Tap No.": "-",
                        "2U - 2V Res(mΩ)": "1.625",
                        "2U - 2V Res (mΩ)": "1.832",
                        "2V - 2W Res (mΩ)": "1.827",
                        "2W - 2V Res (mΩ)": "1.822"
                    }
                ]
            }
        `,
        "Insulation Resistance": `
            Retrieve the Insulation Resistance test data table which contains Test Connection, 15 sec, 1 Min, 10 Min, PI or 15 sec.GΩ, 1 Min.GΩ, 10 Min.GΩ, PI(600s/60s).
            Provide the output in JSON format completely. Also give me the values of OTI and Applied Voltage values.
            Strictly give the values in the JSON format only. Don't give me any other information:
            [
                {
                    "Test connection": "HV/E",
                    "15 sec.GΩ": "7.8",
                    "1Min.GΩ": "8.6",
                    "10Min.GΩ": "16.98",
                    "PI(600s/60s)": "1.97"
                },
                {
                    "Test connection": "LV/E",
                    "15 sec.GΩ": "13.8",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "28.7",
                    "PI(600s/60s)": "1.61"
                },
                {
                    "Test connection": "HV/LV",
                    "15 sec.GΩ": "15.1",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "30.9",
                    "PI(600s/60s)": "1.73"
                }
            ]
        """
    }
}



##################################################  full prompt
{
    "relevant_pages": {
        "DGA": "Analyze the following text and determine if it mentions any information related to oil properties, DGA gases, or Furan values. Specifically, look for the presence of the following parameters: Appearance, Density at 29.5 °C, Breakdown Voltage, Water Content, Neutralisation Value, Resistivity @27°C, Resistivity @90°C, Dielectric Disipation Factor @27°C, Dielectric Disipation Factor @90°C, Interfacial Tension, Flash Point, Sediment & Sludge, TGC Total Gas Content %, Hydrogen (H2), Oxygen (O2), Nitrogen (N2), Carbon monoxide (CO), Carbon dioxide (CO2), Methane (CH4), Ethane (C2H6), Ethylene (C2H4), Acetylene (C2H2), Total Dissolved Combustible Gas (TDCG), TDCG/TGC ( %), 5-Hydroxymethyl-2-furuldehyde, 2-Furfurol (furfuryl alcohol), 2-Furaldehyde, 2-Acetylfuran, 5-Methyl-2-furaldehyde, Total Furans, Estimated DP Value. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Turns Ratio": "Analyze the following text and determine if it mentions any information related to the Insulation Resistance test. Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Winding Resistance": "Analyze the following text and determine if it mentions any information related to the Winding Resistance test. Specifically, look for the presence of tabular data for the following parameters: HV Side Winding Resistance, LV Side Winding Resistance. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Insulation Resistance": "Analyze the following text and determine if it mentions any information related to the Insulation Resistance test. Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'."
    },

    "llm_model_prompts": {
        "DGA": """
            Extract the details of Oil tests, DGA, and Furans from the given text, if the values are not available leave it.
            Ensure to include all the Test Methods, Limits, and Test Values for each parameter.
            Also extract Ambient Humidity and Ambient Temperature from the text.
            Provide the output in JSON format as shown in the example below:
            {
                "Appearance": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Density": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Breakdown Voltage": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Water Content": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Neutralisation Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Interfacial Tension": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Flash Point": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Sediment & Sludge": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TGC Total Gas Content %": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Hydrogen (H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Oxygen (O2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Nitrogen (N2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon monoxide (CO)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon dioxide (CO2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Methane (CH4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethane (C2H6)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethylene (C2H4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Acetylene (C2H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Dissolved Combustible Gas (TDCG)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TDCG/TGC ( %)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Hydroxymethyl-2-furuldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furfurol (furfuryl alcohol)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Acetylfuran": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Methyl-2-furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Furans": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Estimated DP Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Temperature": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Humidity": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Metadata": {
                    "POSITION": ""
                }
            }
            Units are not required to extract.
            If Limits are not provided then you can leave them.
        ,
        "Turns Ratio": 
            Find the Turns Ratio test table and only extract the information of Tap No, MEASURED RATIO, CALCULATED RATIO. Exclude the row from the reverse, u-phase, v-phase, w-phase, ratio error, deviation, error in.
            And provide the output in the json format completely as given in the example. Do not miss any of the Measured Ratio values. Refer to this example json format for response:
            {
                'Tap No.': '1',
                '1U - 1N/ 2U -2W': '9.6512',
                '1V - 1N/ 2U - 2V': '9.6479',
                '1W - 1N/ 2W - 2V': '9.6524',
                'CALCULATED RATIO': '9.6600'
            }
            If only 'Tap No' and 'CALCULATED RATIO' are present, provide the output in the following format:
            {
                'Tap No': '1',
                'CALCULATED RATIO': '9.54'
            }
        ,
        "Winding Resistance": 
            Retrieve the Winding Resistance test data, only extract tables for HV Side and LV Side. Do not extract data for Reverse Order Resistance.
            Provide the output in JSON format completely. Provide all the values from the table. Given below is the example for your reference.
            Do not miss any of the values from HV side and LV Side. Just provide me the json only:
            {
                "Oil Temperature": "40",
                "Reference Temperature": "75",
                "HV": [
                    {
                        "Tap No.": "1",
                        "1U - 1N(mΩ)": "371.5",
                        "1V - 1N(mΩ)": "369.5",
                        "1W - 1N(mΩ)": "369.9"
                    },
                    {
                        "Tap No.": "2",
                        "1U - 1N(mΩ)": "361.2",
                        "1V - 1N(mΩ)": "359.5",
                        "1W - 1N(mΩ)": "362.5"
                    }
                ],
                "LV": [
                    {
                        "Tap No.": "-",
                        "2U - 2V Res(mΩ)": "1.625",
                        "2U - 2V Res (mΩ)": "1.832",
                        "2V - 2W Res (mΩ)": "1"2V - 2W Res (mΩ)": "1.827",
                        "2W - 2V Res (mΩ)": "1.822"
                    }
                ]
            }
        ,
        "Insulation Resistance": 
            Retrieve the Insulation Resistance test data table which contains Test Connection, 15 sec, 1 Min, 10 Min, PI or 15 sec.GΩ, 1 Min.GΩ, 10 Min.GΩ, PI(600s/60s).
            Provide the output in JSON format completely. Also give me the values of OTI and Applied Voltage values.
            Strictly give the values in the JSON format only. Don't give me any other information:
            [
                {
                    "Test connection": "HV/E",
                    "15 sec.GΩ": "7.8",
                    "1Min.GΩ": "8.6",
                    "10Min.GΩ": "16.98",
                    "PI(600s/60s)": "1.97"
                },
                {
                    "Test connection": "LV/E",
                    "15 sec.GΩ": "13.8",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "28.7",
                    "PI(600s/60s)": "1.61"
                },
                {
                    "Test connection": "HV/LV",
                    "15 sec.GΩ": "15.1",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "30.9",
                    "PI(600s/60s)": "1.73"
                }
            ]
        """
    }
}

#################################################################################



########################################### seperate prompts


{
    "relevant_pages": {
        "DGA": "Analyze the following text and determine if it mentions any information related to oil properties, DGA gases, or Furan values. Specifically, look for the presence of the following parameters: Appearance, Density at 29.5 °C, Breakdown Voltage, Water Content, Neutralisation Value, Resistivity @27°C, Resistivity @90°C, Dielectric Disipation Factor @27°C, Dielectric Disipation Factor @90°C, Interfacial Tension, Flash Point, Sediment & Sludge, TGC Total Gas Content %, Hydrogen (H2), Oxygen (O2), Nitrogen (N2), Carbon monoxide (CO), Carbon dioxide (CO2), Methane (CH4), Ethane (C2H6), Ethylene (C2H4), Acetylene (C2H2), Total Dissolved Combustible Gas (TDCG), TDCG/TGC ( %), 5-Hydroxymethyl-2-furuldehyde, 2-Furfurol (furfuryl alcohol), 2-Furaldehyde, 2-Acetylfuran, 5-Methyl-2-furaldehyde, Total Furans, Estimated DP Value. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Turns Ratio": "Analyze the following text and determine if it mentions any information related to the Turns Ratio test. Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Winding Resistance": "Analyze the following text and determine if it mentions any information related to the Winding Resistance test. Specifically, look for the presence of tabular data for the following parameters: HV Side Winding Resistance, LV Side Winding Resistance. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.",
        "Insulation Resistance": "Analyze the following text and determine if it mentions any information related to the Insulation Resistance test. Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values. If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'."
    }
}

###############################################


relevant_pages = {'pages queries': {"DGA": """Analyze the following text and determine if it mentions any information related to oil properties, 
    DGA gases, or Furan values. Specifically, look for the presence of the following parameters: Appearance, 
    Density at 29.5 °C, Breakdown Voltage, Water Content, Neutralisation Value, Resistivity @27°C, Resistivity @90°C,
    Dielectric Disipation Factor @27°C, Dielectric Disipation Factor @90°C, Interfacial Tension, Flash Point, 
    Sediment & Sludge, TGC Total Gas Content %, Hydrogen (H2), Oxygen (O2), Nitrogen (N2), Carbon monoxide (CO), 
    Carbon dioxide (CO2), Methane (CH4), Ethane (C2H6), Ethylene (C2H4), Acetylene (C2H2), 
    Total Dissolved Combustible Gas (TDCG), TDCG/TGC ( %), 5-Hydroxymethyl-2-furuldehyde, 2-Furfurol (furfuryl alcohol),
    2-Furaldehyde, 2-Acetylfuran, 5-Methyl-2-furaldehyde, Total Furans, Estimated DP Value. 
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""" ,
    
    "Turns Ratio": """Analyze the following text and determine if it mentions any information related to the Turns Ratio test. 
    Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values. 
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""",
    
    "Winding Resistance": """Analyze the following text and determine if it mentions any information related to 
    the Winding Resistance test. Specifically, look for the presence of tabular data for the 
    following parameters: HV Side Winding Resistance, LV Side Winding Resistance. 
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""",
    
    "Insulation Resistance": """Analyze the following text and determine if it mentions any information 
    related to the Insulation Resistance test. Specifically, look for the presence of tabular data for the 
    following parameters: Test Connection, 15sec, 1min, 10min, PI values. 
    If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'."""}}




{
"llm_model_prompts": {
        "DGA": """
            Extract the details of Oil tests, DGA, and Furans from the given text, if the values are not available leave it.
            Ensure to include all the Test Methods, Limits, and Test Values for each parameter.
            Also extract Ambient Humidity and Ambient Temperature from the text.
            Provide the output in JSON format as shown in the example below:
            {
                "Appearance": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Density": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Breakdown Voltage": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Water Content": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Neutralisation Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Resistivity @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @27°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Dielectric Disipation Factor @90°C": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Interfacial Tension": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Flash Point": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Sediment & Sludge": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TGC Total Gas Content %": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Hydrogen (H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Oxygen (O2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Nitrogen (N2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon monoxide (CO)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Carbon dioxide (CO2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Methane (CH4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethane (C2H6)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Ethylene (C2H4)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Acetylene (C2H2)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Dissolved Combustible Gas (TDCG)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "TDCG/TGC ( %)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Hydroxymethyl-2-furuldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furfurol (furfuryl alcohol)": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "2-Acetylfuran": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "5-Methyl-2-furaldehyde": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Total Furans": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Estimated DP Value": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Temperature": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Humidity": {"TESTMETHOD": "","LIMITS": "","VALUETEXT": ""},
                "Metadata": {
                    "POSITION": ""
                }
            }
            Units are not required to extract.
            If Limits are not provided then you can leave them.
        ,
        "Turns Ratio": 
            Find the Turns Ratio test table and only extract the information of Tap No, MEASURED RATIO, CALCULATED RATIO. Exclude the row from the reverse, u-phase, v-phase, w-phase, ratio error, deviation, error in.
            And provide the output in the json format completely as given in the example. Do not miss any of the Measured Ratio values. Refer to this example json format for response:
            {
                'Tap No.': '1',
                '1U - 1N/ 2U -2W': '9.6512',
                '1V - 1N/ 2U - 2V': '9.6479',
                '1W - 1N/ 2W - 2V': '9.6524',
                'CALCULATED RATIO': '9.6600'
            }
            If only 'Tap No' and 'CALCULATED RATIO' are present, provide the output in the following format:
            {
                'Tap No': '1',
                'CALCULATED RATIO': '9.54'
            }
        ,
        "Winding Resistance": 
            Retrieve the Winding Resistance test data, only extract tables for HV Side and LV Side. Do not extract data for Reverse Order Resistance.
            Provide the output in JSON format completely. Provide all the values from the table. Given below is the example for your reference.
            Do not miss any of the values from HV side and LV Side. Just provide me the json only:
            {
                "Oil Temperature": "40",
                "Reference Temperature": "75",
                "HV": [
                    {
                        "Tap No.": "1",
                        "1U - 1N(mΩ)": "371.5",
                        "1V - 1N(mΩ)": "369.5",
                        "1W - 1N(mΩ)": "369.9"
                    },
                    {
                        "Tap No.": "2",
                        "1U - 1N(mΩ)": "361.2",
                        "1V - 1N(mΩ)": "359.5",
                        "1W - 1N(mΩ)": "362.5"
                    }
                ],
                "LV": [
                    {
                        "Tap No.": "-",
                        "2U - 2V Res(mΩ)": "1.625",
                        "2U - 2V Res (mΩ)": "1.832",
                        "2V - 2W Res (mΩ)": "1"2V - 2W Res (mΩ)": "1.827",
                        "2W - 2V Res (mΩ)": "1.822"
                    }
                ]
            }
        ,
        "Insulation Resistance": 
            Retrieve the Insulation Resistance test data table which contains Test Connection, 15 sec, 1 Min, 10 Min, PI or 15 sec.GΩ, 1 Min.GΩ, 10 Min.GΩ, PI(600s/60s).
            Provide the output in JSON format completely. Also give me the values of OTI and Applied Voltage values.
            Strictly give the values in the JSON format only. Don't give me any other information:
            [
                {
                    "Test connection": "HV/E",
                    "15 sec.GΩ": "7.8",
                    "1Min.GΩ": "8.6",
                    "10Min.GΩ": "16.98",
                    "PI(600s/60s)": "1.97"
                },
                {
                    "Test connection": "LV/E",
                    "15 sec.GΩ": "13.8",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "28.7",
                    "PI(600s/60s)": "1.61"
                },
                {
                    "Test connection": "HV/LV",
                    "15 sec.GΩ": "15.1",
                    "1Min.GΩ": "17.8",
                    "10Min.GΩ": "30.9",
                    "PI(600s/60s)": "1.73"
                }
            ]
        """
    }
}
