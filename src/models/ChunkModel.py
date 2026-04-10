from requests import session

from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import func,delete

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client=db_client

    @classmethod  #static method to create instance of the model to combine sync init and async init_collection
    async def create_instance(cls,db_client: object):
        instance=cls(db_client)
        return instance

    

    async def create_chunk(self,chunk:DataChunk):
        
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            
            await session.commit()  #commit the transaction to save the chunk to the database
            await session.refresh(chunk) #refresh the chunk instance to get the generated id and other fields
        
        return chunk

    async def get_chunk(self,chunk_id:str):
        
        async with self.db_client() as session:
            async with session.begin():
                query=select(DataChunk).where(DataChunk.chunk_id==chunk_id)
                result=await session.execute(query)
                chunk=result.scalar_one_or_none()
                if chunk is None:
                    return None
        return chunk
    
    async def insert_many_chunks(self, chunks:list, batch_size:int=100):
     
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(chunks),batch_size):

                    batch=chunks[i:i+batch_size]

                    session.add_all(batch) #add_all to add multiple chunk objects to the session

            await session.commit() #commit the transaction to save all chunks to the database
        
        return len(chunks)
        
    async def delete_chunk_by_project_id(self,project_id:ObjectId):
    
        async with self.db_client() as session:
            async with session.begin():
                query=delete(DataChunk).where(DataChunk.chunk_project_id==project_id)
                result=await session.execute(query)
                await session.commit() #commit the transaction to delete the chunks from the database

        return result.rowcount #rowcount to get the number of deleted chunks
    

    async def get_poject_chunks(self,project_id:ObjectId,page_no:int=1,page_size:int=50):
      
        async with self.db_client() as session:
            async with session.begin():
                
                chunks=select(DataChunk).where(DataChunk.chunk_project_id==project_id).offset((page_no-1)*page_size).limit(page_size)
                result=await session.execute(chunks)
                chunk_records=result.scalars().all() #scalars to get the list of chunk objects
        
        return chunk_records