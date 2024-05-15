print("welcome to git")


    preprocessed_data['TESTEDBY'] = data_json['sampled_by']
    preprocessed_data['VALUETEXT'] = preprocessed_data['VALUETEXT'].replace({'NIL': 0, 'BDL': 0, 'N/d' : 0, 'ND' : 0, 'NA' : 0, 'Nil' : 0, '_' : 0})
    preprocessed_data['TESTTYPE'] = "RoutineTest"
    preprocessed_data['SAMPLEDATE'] = pd.to_datetime(preprocessed_data['SAMPLEDATE'])
    preprocessed_data['TESTINGDATE'] = pd.to_datetime(preprocessed_data['TESTINGDATE'])
    # Maintaing the template column order 
    cols = ['SNO','ASSETNAME','TAGNAME','DISPLAYNAME', 'UOM','VALUETEXT', 'TESTMETHOD','SUBSYSTEM','TESTTYPE','SAMPLEDATE', 
            'TESTINGDATE', 'SAMPLEDBY', 'POSITION','POSITION(OTHER)','TESTEDBY','SAMPLINGMETHOD','REASONOFSAMPLING',
