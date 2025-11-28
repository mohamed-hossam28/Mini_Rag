from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId # For MongoDB ObjectId type

class DataChunk(BaseModel):
    id:Optional[ObjectId]=Field(default=None, alias="_id") # MongoDB uses _id as the primary key but in our model we use id
    chunk_text:str=Field(...,min_length=1)
    chunk_metadata:dict
    chunk_order:int=Field(...,gt=0) #order of the chunk in the original document, must be positive integer
    chunk_project_id: ObjectId # Reference to the project this chunk belongs to


    @classmethod  #static method to create inedxes for the collection
    def get_indexes(cls): # Return a list of indexes definations for the collection
        return [
            {
                #key is a list of tuples (field_name, order) and its used to define what fields to index and in what order
                "key":[
                    ("chunk_project_id",1) # 1 for ascending order
                ],
                "name":"chunk_project_id_index_1", # Name of the index
                "unique":False # project_id can have multiple chunks
            }
        ]

    class Config:
        arbitrary_types_allowed = True# Allow ObjectId type because its not a standard type to pydantic