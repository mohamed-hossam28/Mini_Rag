from .mini_rag_base import SQLAlchemyBase
from sqlalchemy import Column, String, Integer, DateTime, Text,ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid
from pydantic import BaseModel



class DataChunk(SQLAlchemyBase):
    __tablename__ = 'chunks'

    chunk_id=Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid=Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    chunk_text=Column(String, nullable=False)
    chunk_metadata=Column(JSONB, nullable=False)    #jsonb to store in binary so that the reading is faster and also allows for indexing
    chunk_order=Column(Integer, nullable=False) #order of the chunk in the original document, must be positive integer

    chunk_project_id=Column(Integer,ForeignKey("projects.project_id"),nullable=False,)
    chunk_asset_id=Column(Integer,ForeignKey("assets.asset_id"),nullable=False,)

    #######Relationships########
    project=relationship("Project", back_populates="chunks")
    assets=relationship("Asset", back_populates="chunks")

    #######INDEXING########
    __table_args__ = (
        Index('ix_chunk_project_id', 'chunk_project_id'),
        Index('ix_chunk_asset_id', 'chunk_asset_id'),
        Index('ix_chunk_order', 'chunk_order'),
        Index('ix_chunk_project_id_order', 'chunk_project_id', 'chunk_order')
    )


class RetrievedDocument(BaseModel):
    text: str
    score: float