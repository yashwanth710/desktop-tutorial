def return_vector_db(name:str, **kw):
    """Return vector db of given choise."""
    if name == "chroma":
        from vector_store.chroma_db import ChromaVectorDB
        vector_db = ChromaVectorDB(**kw)
        return vector_db

    elif name == "qdrant":
        from vector_store.qdrant_db import QdrantVectorDB
        vector_db = QdrantVectorDB(**kw)
        return vector_db
    else:
        raise ValueError("invalid vector db given.")
