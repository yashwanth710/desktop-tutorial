prompts = {
    'page_queries': {
        'Turns Ratio': """Analyze the following text and determine if it mentions any information related to the Insulation Resistance test.
Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values.
If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""",

        'Winding Resistance': """Analyze the following text and determine if it mentions any information related to the Winding Resistance test.
Specifically, look for the presence of tabular data for the following parameters: HV Side Winding Resistance, LV Side Winding Resistance.
If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'.""",

        'Insulation Resistance': """Analyze the following text and determine if it mentions any information related to the Insulation Resistance test.
Specifically, look for the presence of tabular data for the following parameters: Test Connection, 15sec, 1min, 10min, PI values.
If any of these parameters are present, respond 'Yes'; otherwise, respond 'No'."""
    },
    
    

    'model_queries': {
        'Turns Ratio': """Find the Turns Ratio test table and only extract the information of Tap No, MEASURED RATIO, CALCULATED RATIO. Exclude the row from the reverse, u-phase, v-phase, w-phase, ratio error, deviation, error in.
And provide the output in the json format completely as given in the example. Do not miss any of the Measured Ratio values. Refer to this example json format for response.
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
}""",
        
        'Winding Resistance': """Retrieve the Winding Resistance test data, only extract tables for HV Side and LV Side. Do not extract data for Reverse Order Resistance.
Provide the output in JSON format completely.
Provide all the values from the table. Given below is the example for your reference.
Do not miss any of the values from HV side and LV Side. Just provide me the json only. 
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
}""",

        'Insulation Resistance': """Retrieve the Insulation Resistance test data table which contains Test Connection, 15 sec, 1 Min, 10 Min, PI or 15 sec.GΩ, 1 Min.GΩ, 10 Min.GΩ, PI(600s/60s).
Provide the output in JSON format completely. Also give me the values of OTI and Applied Voltage values.
Strictly give the values in the JSON format only. Don't give me any other information.
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
]"""
    }
}
