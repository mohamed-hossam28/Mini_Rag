from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection=self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    async def create_chunk(self,chunk:DataChunk):
        result= await self.collection.insert_one(chunk.dict(by_alias=True,exclude_unset=True)) 
        #by alias to use field aliases like _id, exclude_unset to avoid inserting unset optional fields
        
        chunk._id=result.inserted_id
        return chunk

    async def get_chunk(self,chunk_id:str):
        result=await self.collection.find_one({
            "_id":ObjectId(chunk_id)
        }) 

        if result is None:
            return None
        
        return DataChunk(**result)
    
    async def insert_many_chunks(self, chunks:list, batch_size:int=100):
        for i in range(0,len(chunks),batch_size):

            batch=chunks[i:i+batch_size]

            operations=[
                InsertOne(chunk.dict(by_alias=True,exclude_unset=True)) for chunk in batch
            ]
            #InsertOne represents one MongoDB insert command, but instead of executing it immediately, you store it as an operation.

            await self.collection.bulk_write(operations)

        return len(chunks)
    
    async def delete_chunk_by_project_id(self,project_id:ObjectId):
        result=await self.collection.delete_many({
            "project_id":project_id
        })

        return result.deleted_count



