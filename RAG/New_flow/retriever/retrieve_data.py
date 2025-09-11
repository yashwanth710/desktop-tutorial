from typing import List, Any
from langchain_core.documents import Document


class Retriever:
    def __init__(self, retriever: Any):
        self.retriever = retriever

    async def retrieve(self, query: str, **kwargs) -> List[Document]:
            return await self.retriever.ainvoke(query, **kwargs)
        