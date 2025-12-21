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

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str
    OPENAI_API_URL: str
    
    COHERE_API_KEY: str

    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str
    EMBEDDING_MODEL_SIZE: int

    INPUT_DAFAULT_MAX_CHARACTERS: int
    GENERATION_DAFAULT_MAX_TOKENS: int
    GENERATION_DAFAULT_TEMPERATURE: float


    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str

    PRIMARY_LANG: str
    DEFAULT_LANG: str

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