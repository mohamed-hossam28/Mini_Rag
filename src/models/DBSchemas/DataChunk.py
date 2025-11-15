from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId # For MongoDB ObjectId type

class DataChunk(BaseModel):
    id:Optional[ObjectId]=Field(default=None, alias="_id") # MongoDB uses _id as the primary key
    chunk_text:str=Field(...,min_length=1)
    chunk_metadata:dict
    chunk_order:int=Field(...,gt=0) #order of the chunk in the original document, must be positive integer
    chunk_project_id: ObjectId # Reference to the project this chunk belongs to


    class Config:
        arbitrary_types_allowed = True# Allow ObjectId type because its not a standard type to pydantic