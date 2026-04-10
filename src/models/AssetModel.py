from sqlalchemy import select,delete

from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import Asset


class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client=db_client

    @classmethod  #static method to create instance of the model to combine sync init and async init_collection
    async def create_instance(cls,db_client: object):
        instance=cls(db_client)
        return instance


    async def create_asset(self,asset:Asset):
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            
            await session.commit()  #commit the transaction to save the asset to the database
            await session.refresh(asset) #refresh the asset instance to get the generated id and other fields
        return asset
    
    async def get_all_project_asset(self,asset_project_id:str,asset_type:str):
        
        async with self.db_client() as session:
            async with session.begin():
                query=select(Asset).where(
                    Asset.asset_project_id==asset_project_id,
                    Asset.asset_type==asset_type
                )
                result=await session.execute(query)
                assets=result.scalars().all() #scalars to get the list of asset objects
                return assets
        
    async def delete_asset_by_project_id(self,project_id:str):

        async with self.db_client() as session:
            async with session.begin():
                query=delete(Asset).where(Asset.asset_project_id==project_id)
                result=await session.execute(query)
                await session.commit() #commit the transaction to delete the assets from the database
        
        return result.rowcount #rowcount to get the number of deleted assets

    async def get_asset_record(self,asset_project_id:str,asset_name:str):

        async with self.db_client() as session:
            async with session.begin():
                query=select(Asset).where(
                    Asset.asset_project_id==asset_project_id,
                    Asset.asset_name==asset_name
                )
                result=await session.execute(query)
                asset=result.scalar_one_or_none() #scalar_one_or_none to get one result or None if not found
        
        return asset
