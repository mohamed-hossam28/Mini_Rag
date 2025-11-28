from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import Project

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection=self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]


    async def init_collection(self):
        all_collections=await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_PROJECT_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value] #create collection
            indexes=Project.get_indexes() #get indexes schema from Project 
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

    
    async def create_project(self,project:Project):
        result=await self.collection.insert_one(project.dict())  #insert_one only accepts dict
        project._id=result.inserted_id

        return project
    
    async def get_project_or_create_one(self,project_id:str):
        record=await self.collection.find_one({
            "project_id": project_id
        })
        
        if record is None:
            project=Project(project_id=project_id)
            project=await self.create_project(project)
            return project
        
        return Project(**record)   #unpack the record dict into project model
    

    async def get_all_projects(self,page:int=1,page_size:int=10):
    #instead of loading all at once and exhausting memory load it page by page each page have page_size items
        total_documents=await self.collection.count_documents({}) #get total number of documents
        #calculate number of pages
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor=self.collection.find().skip( (page-1) * page_size ).limit(page_size)
        #cursor for pointing to the documents and not loading all at once
        projects=[]
        async for document in cursor:
            projects.append(
                Project(**document)
            )

        return projects,total_pages
