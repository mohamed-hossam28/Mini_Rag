from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .DBSchemas import Project
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client=db_client

    @classmethod  #static method to create instance of the model to combine sync init and async init_collection
    async def create_instance(cls,db_client: object):
        instance=cls(db_client)
        return instance

    
    async def create_project(self,project:Project):
        
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            
            await session.commit()  #commit the transaction to save the project to the database
            await session.refresh(project) #refresh the project instance to get the generated id and other fields

        return project
    
    async def get_project_or_create_one(self,project_id:str):
        async with self.db_client() as session:
            async with session.begin():
                query=select(Project).where(Project.project_id==int(project_id))
                result=await session.execute(query)
                project=result.scalar_one_or_none() #scalar_one_or_none to get one result or None if not found
                if project is None:
                    project_rec=Project(project_id=int(project_id))
                    
                    project=await self.create_project(project_rec) #create the project if not found
                    return project
                else:
                    return project
                
    
    async def get_all_projects(self,page:int=1,page_size:int=10):
        
        async with self.db_client() as session:
            async with session.begin():

                total_documents=await session.execute(
                    func.count(Project.project_id) #count the total number of projects
                )
                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1
                
                query=select(Project).offset( (page-1) * page_size ).limit(page_size) #offset to skip the previous pages and limit to get only page_size projects
                result=await session.execute(query)
                projects=result.scalars().all() #scalars to get the list of project objects
                return projects,total_pages