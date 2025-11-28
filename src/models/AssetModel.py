from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import Asset
from bson.objectid import ObjectId


class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection=self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]


    async def init_collection(self):
        all_collections=await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value] #create collection
            indexes=Asset.get_indexes() #get indexes schema from Project 
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


    async def create_asset(self,asset:Asset):
        result=await self.collection.insert_one(asset.dict(by_alias=True,exclude_unset=True)) 
        asset.id=result.inserted_id
        return asset

    async def get_all_project_asset(self,asset_project_id:str,asset_type:str):
        records=await self.collection.find({
            "asset_project_id":ObjectId(asset_project_id)if isinstance(asset_project_id,str) else asset_project_id,
            "asset_type":asset_type
        }).to_list(length=None)

        return [Asset(**record) for record in records]

    
    async def delete_asset_by_project_id(self,project_id:str):
        result=await self.collection.delete_many({
            "asset_project_id":ObjectId(project_id)if isinstance(project_id,str) else project_id
        })

        return result.deleted_count

    async def get_asset_record(self,asset_project_id:str,asset_name:str):
        record=await self.collection.find_one({
            "asset_project_id":ObjectId(asset_project_id)if isinstance(asset_project_id,str) else asset_project_id,
            "asset_name":asset_name
        })

        if record is None:
            return None

        return Asset(**record)
