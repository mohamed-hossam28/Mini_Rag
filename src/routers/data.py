from fastapi import APIRouter,Depends,UploadFile,status,Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController,ProjectsController,ProcessController
import aiofiles
from models import ResponseSignals, ProjectModel, ChunkModel,AssetModel,AssetTypeEnum
from models.DBSchemas import Project, DataChunk,Asset
import logging
from .schemas import ProcessRequest
from bson.objectid import ObjectId

logger = logging.getLogger('uvicorn.error')

data_router=APIRouter(
    prefix="/data",
    tags=["data"]
)

#validate file propirties
@data_router.post("/upload/{project_id}") #project_id is dynamic to identify different projects
async def upload_data(request:Request,project_id: str, file: UploadFile , app_settings : Settings =Depends(get_settings)):
    #Request is needed to access the request object(app variables) if needed
    
    data_controller=DataController()

    is_valid, signal= data_controller.validate_uploaded_file(file)
     
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'Signal':signal
            }
        )
    
    #create project in DB if not exists
    project_model=await ProjectModel.create_instance(request.app.db_client)
    project=await project_model.get_project_or_create_one(project_id=project_id)
    
    #craete project directory if not exists
    project_dir_path=ProjectsController().get_project_path(project_id)

    file_path, file_id=data_controller.generate_unique_filepath(
        original_file_name=file.filename,
        project_id=project_id
    )
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):  # Read file in chunks
                await f.write(chunk)

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'Signal':ResponseSignals.FILE_UPLOAD_FAILED.value
            }
        )

    asset_model=await AssetModel.create_instance(request.app.db_client)

    asset_recource=Asset(
        asset_project_id=ObjectId(project.id),
        asset_name=file_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_size=os.path.getsize(file_path)
    )

    asset_record=await asset_model.create_asset(asset_recource)

    if asset_record is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'Signal':ResponseSignals.FILE_UPLOAD_FAILED.value
            }
        )

    return JSONResponse(
            content={
                "signal": ResponseSignals.FILE_UPLOAD_SUCCESS.value,
                "file_id": str(asset_record.id)
            }
        )

    
@data_router.post("/process/{project_id}") #project_id is dynamic to identify different projects
async def process_endpoint(request:Request, project_id:str ,process_reqquest:ProcessRequest) :
    #get processing parameters
    file_id=process_reqquest.file_id
    chunk_size=process_reqquest.chunk_size
    overlap_size=process_reqquest.overlap_size
    do_reset=process_reqquest.do_reset

    #process the file
    process_controller=ProcessController(project_id=project_id)

    file_content=process_controller.get_file_content(file_id=file_id)

    chunks=process_controller.process_file_content(
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    if chunks is None or len(chunks) ==0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'Signal':ResponseSignals.FILE_PROCESSING_FAILED.value
            }
        )
    
    #store chunks in DB
        #get project
    project_model=await ProjectModel.create_instance(request.app.db_client)
    project=await project_model.get_project_or_create_one(project_id=project_id)

        #add chunk
    chunk_model=await ChunkModel.create_instance(request.app.db_client)
    file_chunks_records=[
        DataChunk(
            chunk_text=chunck.page_content,
            chunk_metadata=chunck.metadata,
            chunk_order=i+1,
            chunk_project_id=project.id
        )
        for i ,chunck in enumerate(chunks)
    ]
     #check do reset to remove previous chunks or not
    if do_reset == 1:
        _=await chunk_model.delete_chunk_by_project_id(project_id=project.id)

    no_records=await chunk_model.insert_many_chunks(
        chunks=file_chunks_records
    ) 


    return JSONResponse(
        content={
            "signal": ResponseSignals.FILE_PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records
        }
    )
