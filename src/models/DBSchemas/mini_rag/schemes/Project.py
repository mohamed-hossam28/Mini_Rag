from .mini_rag_base import SQLAlchemyBase
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid



class Project(SQLAlchemyBase):
    __tablename__ = 'projects'

    project_id= Column(Integer,primary_key=True,autoincrement=True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False,server_default='now()')
    updated_at = Column(DateTime(timezone=True), nullable=False,onupdate='now()')


    #######Relationships########
    assets=relationship("Asset", back_populates="project") #one to many relationship with assets, one project can have multiple assets but each asset belongs to only one project
    chunks=relationship("DataChunk", back_populates="project") #one to many relationship with chunks, one project can have multiple chunks but each chunk belongs to only one project
    

    