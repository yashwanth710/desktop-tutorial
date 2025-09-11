from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_redis import RedisChatMessageHistory
from models.openai import OpenAIModel
from utils.settings import settings
from prompts.prompt_utils import format_prompt

async def init_history(redis_history):
    if not await redis_history.aget_messages():
        await redis_history.aadd_messages([SystemMessage(content = "You are helpful assistant")])

class RAGLLM():
    def __init__(self, session_id):
        self.model = OpenAIModel()
        self.chat_history = RedisChatMessageHistory(session_id= session_id,
                                                    redis_url= settings.redis_url)
        
    async def format_chat_history(self):
        """
        Takes RedisChatMessageHistory and format history of User and AI messages.
        This history is being used in Query Transformation.
        """
        formatted_messages = []
        try:
            for message in await self.chat_history.aget_messages():
                if isinstance(message, HumanMessage):
                    formatted_messages.append(f"User : {message.content}")
                elif isinstance(message, AIMessage):
                    formatted_messages.append(f"AI : {message.content}")
        except Exception as redis_format_error:
            print(f"Error in redis chat fromatting: {redis_format_error}")
            return ""
        return "\n".join(formatted_messages)

        
    async def generate(self, query:str, context: str):
        try:
            rag_prompt = format_prompt("RAG_PROMPT")
            system_message = SystemMessage(content=rag_prompt)
            human_message = HumanMessage(content=f"""Context:\n{context}\n\nUser Query:\n{query}""")
            history_messages = await self.chat_history.aget_messages()
            messages = [system_message] + history_messages + [human_message]
        
            response =  await self.model.invoke(messages)
            await self.chat_history.aadd_messages([
                                                HumanMessage(content=query),
                                                AIMessage(content=response)
                                                ])
            return response
        except Exception as generate_error:
            print(f"Error in generating answer: {generate_error}")
    
    async def transform_query(self,query:str) -> str:
        """Takes a user query and rewrites it to be clearer and more specific using chat context for better retrieval"""
        try:
            formatted_chat_history = await self.format_chat_history()
            query_transform_prompt = format_prompt("QUERY_TRANSFORMATION_PROMPT",
                                                chat_history = formatted_chat_history,
                                                latest_user_query = query)
            messages = [HumanMessage(content=query_transform_prompt)]
            transformed_query = await self.model.invoke(messages)
            return transformed_query
        except Exception as transform_error:
            print("Issue in transforming the query. so passing original user query to retrieval.")
            print(f"Error: {transform_error}")
            return query
    

    




