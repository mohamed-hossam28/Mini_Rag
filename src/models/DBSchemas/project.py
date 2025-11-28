from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId # For MongoDB ObjectId type

class Project(BaseModel):
    id: Optional[ObjectId]=Field(default=None, alias="_id") # MongoDB uses _id as the primary key
    project_id:str=Field(...,min_length=1)

    
    @validator('project_id') #static method to validate project_id
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        return value
    
    @classmethod  #static method to create inedxes for the collection
    def get_indexes(cls): # Return a list of indexes definations for the collection
        return [
            {
                #key is a list of tuples (field_name, order) and its used to define what fields to index and in what order
                "key":[
                    ("project_id",1) # 1 for ascending order
                ],
                "name":"project_id_index_1", # Name of the index
                "unique":True # Ensure project_id is unique
            }
        ]

    class Config:
        arbitrary_types_allowed = True# Allow ObjectId type because its not a standard type to pydantic