from fastapi import APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController,ProjectsController,ProcessController
import aiofiles
from models import ResponseSignals
import logging
from .schemas import ProcessRequest

logger = logging.getLogger('uvicorn.error')

data_router=APIRouter(
    prefix="/data",
    tags=["data"]
)

#validate file propirties
@data_router.post("/upload/{project_id}") #project_id is dynamic to identify different projects
async def upload_data(project_id: str, file: UploadFile , app_settings : Settings =Depends(get_settings)):
    
    data_controller=DataController()

    is_valid, signal= data_controller.validate_uploaded_file(file)
     
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'Signal':signal
            }
        )
    
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
    return JSONResponse(
            content={
                "signal": ResponseSignals.FILE_UPLOAD_SUCCESS.value,
                "file_id": file_id
            }
        )

    
@data_router.post("/process/{project_id}") #project_id is dynamic to identify different projects
async def process_endpoint(project_id:str ,process_reqquest:ProcessRequest) :
    file_id=process_reqquest.file_id
    chunk_size=process_reqquest.chunk_size
    overlap_size=process_reqquest.overlap_size

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
    
    serialized_chunks = [
    {
        "content": chunk.page_content,
        "metadata": chunk.metadata
    }
    for chunk in chunks
]

    return JSONResponse(
        content={
            "signal": ResponseSignals.FILE_PROCESSING_SUCCESS.value,
            "chunks": serialized_chunks
        }
    )
