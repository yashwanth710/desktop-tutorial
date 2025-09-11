from dataclasses import dataclass
from typing import  Dict, Any, TypedDict, Literal


@dataclass
class FullPageData:
    content: str
    metadata: Dict[str, Any]

@dataclass
class ChunkData:
    content: str
    metadata: Dict[str, Any]

class ParentMetaData(TypedDict):
    source : str
    page: int
    chunk_number: int
    type: str
    chunk_type: str     #parent always

class ChildMetaData(TypedDict):
    source: str
    page: int
    type: str
    parent_id: int      # refers to chunk_number in ParentMetaData
    child_id: int
    chunk_type: str     #child always


@dataclass
class ParentChunk:
    content: str
    metadata: ParentMetaData

@dataclass
class ChildChunk:
    content: str
    metadata: ChildMetaData




