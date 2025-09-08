import uuid
from typing import List, Dict, Any, Tuple

def generate_chunk_id(page_num: int, chunk_index: int) -> str:
    """Generate unique chunk ID"""
    return f"page_{page_num}_chunk_{chunk_index}"

def format_sources(similar_chunks: List[Dict]) -> List[Dict]:
    """Format source information for display"""
    return [
        {
            'page': chunk['page_number'],
            'text_preview': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
            'has_visuals': chunk['has_visuals'],
            'relevance_score': chunk['score']
        }
        for chunk in similar_chunks
    ]

def build_context(similar_chunks: List[Dict]) -> str:
    """Build context string from similar chunks"""
    context_parts = []
    for chunk in similar_chunks:
        context_part = f"Page {chunk['page_number']}: {chunk['text']}"
        if chunk['has_visuals']:
            context_part += " [Contains visual elements]"
        context_parts.append(context_part)
    
    return "\n\n".join(context_parts)