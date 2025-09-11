from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.messages import HumanMessage, BaseMessage
from typing import List

from utils.settings import settings
from prompts.prompt_utils import  format_prompt


class OpenAIModel:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_endpoint,
            azure_deployment=settings.deployment_name,
            api_version=settings.llm_api_version,
            api_key=settings.azure_openai_key,
        )

    async def invoke(self, messages: List[BaseMessage]) -> str:
        try:
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
        except Exception as e:
            print(f"Error invoking OpenAI model: {e}")
            raise


class OpenAIEmbedModel:
    def __init__(self):
        self.model = AzureOpenAIEmbeddings(
            azure_endpoint=settings.embed_deployment_endpoint,
            azure_deployment=settings.embed_deployment_name,
            api_version=settings.embed_api_version,
            api_key=settings.azure_openai_key
        )


class OpenAIVisionModel:
    def __init__(self):
        self.model = AzureChatOpenAI(
            azure_endpoint=settings.vision_endpoint,
            azure_deployment=settings.vision_deployment_name,
            api_version=settings.vision_api_version,
            api_key=settings.azure_openai_key,
        )

    async def generate(self, messages: List[BaseMessage]) -> str:
        try:
            response = await self.model.ainvoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating vision model response: {e}")
            raise

    


class VisionModelWrapper:
    """Wrapper that prepares inputs for the OpenAIVisionModel and handles base64 + prompt."""

    def __init__(self):
        self.model = OpenAIVisionModel()

    async def run(self, b64_image: str) -> str:
        try:
            image_url = f"data:image/png;base64,{b64_image}" 
            prompt = format_prompt("IMAGE_EXTRACTION_PROMPT_FULL")
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ])
            return await self.model.generate([message])
        except Exception as e:
            print(f"Exception in VisionModelWrapper: {e}")
            raise 
