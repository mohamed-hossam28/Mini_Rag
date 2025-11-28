from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection=self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]


    async def init_collection(self):
        all_collections=await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value] #create collection
            indexes=DataChunk.get_indexes() #get indexes schema from Project 
            for index in indexes:#loop through each index and create it in the collection
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index.get("unique", False)
                )

    @classmethod  #static method to create instance of the model to combine sync init and async init_collection
    async def create_instance(cls,db_client: object):
        instance=cls(db_client)
        await instance.init_collection()
        return instance

    

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



