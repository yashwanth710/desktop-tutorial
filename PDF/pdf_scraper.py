from datetime import datetime
from openai import OpenAI
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from prompts import prompts
import os
from pdf_processing import  extract_text_from_pdf, table_extraction
import json 
import pandas as pd
import fitz


def is_relevant(text, prompt, client):
    
    # Make an API call to OpenAI's GPT-3.5-turbo model to check if the text is relevant
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"'{prompt}':\n\n context: {text}\n\nAnswer with 'Yes' or 'No'."}]
    )
    
    # Return True if the response is 'Yes', otherwise False
    return response.choices[0].message.content.strip().lower() == 'yes'



def find_relevant_pages(pdf_path, prompt, client):
     # Extract text from the PDF document
    text_by_page = extract_text_from_pdf(pdf_path)
    relevant_pages = []
    # Iterate through each page's text
    for page_number, text in text_by_page.items():
        # Check if the text is relevant to the given prompt
        if is_relevant(text, prompt, client):
             # If relevant, add the page number to the list
            relevant_pages.append(page_number)
    
    return relevant_pages


os.environ["OPENAI_API_KEY"] = "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"



# Initialize the OpenAI GPT-4 model for chat
chat_llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

def model_data(data):    
    # Initialize the OpenAI GPT-4 model for chat
    chat_llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    query = prompts['model queries']['DGA']
    # Combine the query and document content
    combined_query = query + "\n\nDocument Content:\n" + data
    start_time = datetime.now()

    # Generate a completion
    response = chat_llm.predict(text=combined_query) # Use predict() instead of chat() for ChatOpenAI
    end_time = datetime.now()
#     print('Duration: {}'.format(end_time - start_time))
    
    return response
