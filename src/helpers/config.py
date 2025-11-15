from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from pydantic import field_validator

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str

    FILE_MAX_SIZE: int
    
    #  Use Annotated[..., NoDecode] to force Pydantic to skip 
    FILE_ALLOWED_TYPES: Annotated[list[str], NoDecode] 
    
    FILE_DEFAULT_CHUNK_SIZE: int  # kb to load chunk from memory to directory in bytes

    MONGODB_URL: str
    MONGODB_DATABASE: str

    @field_validator('FILE_ALLOWED_TYPES', mode='before')
    @classmethod
    def _split_allowed_types(cls, v):
        # This custom validator splits the comma-separated string into a list.
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v 

    model_config = SettingsConfigDict(
        env_file=".env"
    )

def get_settings():
    return Settings()