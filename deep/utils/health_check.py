# utils/health_check.py
import requests
import streamlit as st
from config.settings import settings

def check_qdrant_connection():
    """Check if Qdrant is running and accessible"""
    try:
        response = requests.get(f"{settings.QDRANT_URL}/collections")
        if response.status_code == 200:
            return True, "Qdrant is connected successfully!"
        else:
            return False, f"Qdrant returned status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Qdrant. Please make sure it's running."
    except Exception as e:
        return False, f"Error connecting to Qdrant: {str(e)}"

def get_qdrant_info():
    """Get information about Qdrant collections"""
    try:
        response = requests.get(f"{settings.QDRANT_URL}/collections")
        if response.status_code == 200:
            collections = response.json().get('collections', [])
            return {
                'status': 'connected',
                'collections_count': len(collections),
                'collections': [col['name'] for col in collections]
            }
        return {'status': 'error', 'message': f"Status code: {response.status_code}"}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}