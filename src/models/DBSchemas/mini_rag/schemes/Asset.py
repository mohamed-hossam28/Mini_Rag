from .mini_rag_base import SQLAlchemyBase
from sqlalchemy import Column, String, Integer, DateTime, Text,ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid



class Asset(SQLAlchemyBase):
    __tablename__ = 'assets'

    asset_id=Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid=Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    asset_name=Column(String, nullable=False)   #example file_id
    asset_type=Column(String, nullable=False)   #example file or UnboundLocalError
    asset_size=Column(Integer, nullable=False)
    asset_config=Column(JSONB, nullable=True)    #jsonb to store in binary so that the reading is faster and also allows for indexing
    
    asset_created_at=Column(DateTime(timezone=True), server_default='now()',nullable=False)
    asset_updated_at=Column(DateTime(timezone=True), onupdate='now()')

    asset_project_id=Column(Integer,ForeignKey("projects.project_id"),nullable=False,)

    #######Relationships########
    project=relationship("Project", back_populates="assets")
    chunks=relationship("DataChunk", back_populates="assets") #one to many relationship with chunks, one asset can have multiple chunks but each chunk belongs to only one asset
    
    #######INDEXING########
    __table_args__ = (
        Index('ix_asset_project_id', 'asset_project_id'),
        Index('ix_asset_type', asset_type),
        Index("ix_asset_name",asset_name),
        Index('ix_asset_project_id_name', 'asset_project_id', 'asset_name', unique=True)
    )
