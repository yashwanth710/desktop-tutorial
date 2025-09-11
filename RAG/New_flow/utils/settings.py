from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import pydantic_core
import logging

class Settings(BaseSettings):
    openai_api_key: str = Field(...,validation_alias='OPENAI_API_KEY')
    port: int = Field(...,validation_alias = 'PORT')
    openai_model: str = Field(...,validation_alias='OPENAI_MODEL')
    openai_embed_model:str = Field(..., validation_alias='OPENAI_EMBED_MODEL')
    redis_url: str = Field(...,validate_alias = 'REDIS_URL')
    azure_openai_key:str = Field(...,validation_alias = 'AZURE_OPENAI_API_KEY')
    deployment_name : str = Field(...,validation_alias= 'DEPLOYMENT_NAME')
    azure_endpoint : str = Field(..., validation_alias = 'DEPLOYMENT_URL_GPT_MINI')
    llm_api_version : str = Field(..., validation_alias= 'MODEL_API_VERSION')
    embed_api_version : str = Field(..., validation_alias= 'EMBED_API_VERSION')
    embed_deployment_name:str = Field(...,validation_alias= 'EMBED_DEPLOYMENT_NAME')
    embed_deployment_endpoint : str = Field(..., validation_alias= 'DEPLOYMENT_URL_EMBEDDING')
    vision_api_version:str = Field(..., validation_alias= 'VISION_API_VERSION')
    vision_deployment_name:str = Field(..., validation_alias='VISION_DEPLOYMENT_NAME')
    vision_endpoint:str = Field(...,validation_alias= 'DEPLOYMENT_URL_GPT4O')
    mistral_api_key :str = Field(..., validation_alias= 'MISTRAL_API_KEY')



    model_config = {
        "env_file" : ".env",
        "env_file_encoding" : "utf-8",
        "extra" : "allow"
                    } 

    def __init__(self, **values):
        try:
            super().__init__(**values)
        except pydantic_core._pydantic_core.ValidationError as e:
            missing_fields = []
            for error in e.errors():
               if error["type"] == "missing":
                   missing_fields.append(error["loc"][0])
                   
            print(f"Following fields missed : {", ".join(missing_fields)}")
            raise 

settings = Settings()

           
           
            