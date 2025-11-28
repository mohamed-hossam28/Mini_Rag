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
    
    chunk_size=process_reqquest.chunk_size
    overlap_size=process_reqquest.overlap_size
    do_reset=process_reqquest.do_reset

    #get project
    project_model=await ProjectModel.create_instance(request.app.db_client)
    project=await project_model.get_project_or_create_one(project_id=project_id)
    #init models
    process_controller=ProcessController(project_id=project_id)
    asset_model=await AssetModel.create_instance(request.app.db_client)
    chunk_model=await ChunkModel.create_instance(request.app.db_client)

    #get files id from db 
    project_file_ids={}
    if process_reqquest.file_id :
        asset_record=await asset_model.get_asset_record(
            asset_project_id=ObjectId(project.id),
            asset_name=process_reqquest.file_id
        )
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'Signal':ResponseSignals.FILE_ID_ERROR.value
                }
            )

        project_file_ids={
            asset_record.id:asset_record.asset_name
        }
    else:
        project_file=await asset_model.get_all_project_asset(
            asset_project_id=ObjectId(project.id),
            asset_type=AssetTypeEnum.FILE.value
        )
        project_file_ids={
            record.id:record.asset_name
            for record in project_file
        }
        if len(project_file_ids) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'Signal':ResponseSignals.NO_FILES_ERROR.value
                }
            )
        
    #process files
    #check do reset to remove previous chunks or not
    if do_reset == 1:
        _=await chunk_model.delete_chunk_by_project_id(project_id=project.id)

    no_records=0
    no_files=0
    
    for asset_id,file_id in project_file_ids.items():
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
        file_chunks_records=[
            DataChunk(
                chunk_text=chunck.page_content,
                chunk_metadata=chunck.metadata,
                chunk_order=i+1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id
            )
            for i ,chunck in enumerate(chunks)
        ]

        no_records+=await chunk_model.insert_many_chunks(
            chunks=file_chunks_records
        ) 
        no_files+=1


    return JSONResponse(
        content={
            "signal": ResponseSignals.FILE_PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )
