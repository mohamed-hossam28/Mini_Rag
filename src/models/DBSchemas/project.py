from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId # For MongoDB ObjectId type

class Project(BaseModel):
    id: Optional[ObjectId]=Field(default=None, alias="_id") # MongoDB uses _id as the primary key
    project_id:str=Field(...,min_length=1)

    @validator('project_id')
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        return value
    

    class Config:
        arbitrary_types_allowed = True# Allow ObjectId type because its not a standard type to pydantic