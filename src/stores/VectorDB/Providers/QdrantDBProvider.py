from sqlalchemy.sql._elements_constructors import true
from numba.core.types import none
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from qdrant_client import QdrantClient,models

class QdrantDBProvider(VectorDBInterface):
    def __init__(self,dp_path:str,distance_method:str):
        self.client=None
        self.dp_path=dp_path
        
        if distance_method==DistanceMethodEnums.COSINE.value:
            self.distance_method=DistanceMethodEnums.COSINE.value
        elif distance_method==DistanceMethodEnums.DOT.value:
            self.distance_method=DistanceMethodEnums.DOT.value

        self.logger=logging.getLogger(__name__)

    def connect(self):
        self.client=QdrantClient(path=self.dp_path)

    def disconnect(self):
        self.client=None

    def is_collection_existed(self,collection_name:str)->bool:
        return self.client.collection_exists(collection_name)
    
    def list_collections(self)->List:
        return self.client.get_collections()
    
    def get_collection_info(self,collection_name:str)->dict:
        if self.is_collection_existed(collection_name):
            return self.client.get_collection(collection_name)
        else:
            self.logger.error(f"Collection {collection_name} does not exist")
            return None

    def delete_collection(self,collection_name:str):
        if self.is_collection_existed(collection_name):
            self.client.delete_collection(collection_name)

    def create_collection(self,collection_name:str,embedding_size:int,do_reset:bool=False):

        if do_reset:
            _=self.delete_collection(collection_name)
        
        if not self.is_collection_existed(collection_name):
            _=self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method,
                )
            )
            return True
        else:
            self.logger.error(f"Collection {collection_name} already exists")
            return False

    def insert_one(self,collection_name:str,vector:list,text:str,
                    metadata:dict=None,record_id:str=None):
        
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        try:
            _=self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        vector=vector,
                        payload={
                            "text":text,
                            "metadata": metadata
                        }
                    )
                ]
            )
            return True

        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False


    def insert_many(self,collection_name:str,text:list,vector:list,
                    metadata:list=None,record_ids:list=None,batch_size:int=50):

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        #if metadata is none then make it a list of none to iterate over it
        if metadata is None:
            metadata=[None]*len(text)
        
        if record_ids is None:
            record_ids=[None]*len(text) 

        for i in range(0,len(text),batch_size):
            batch_end=i+batch_size

            batch_text=text[i:batch_end]
            batch_vector=vector[i:batch_end]
            batch_metadata=metadata[i:batch_end]

            batch_record=[
                models.Record(
                    vector=batch_vector[x],
                    payload={
                        "text":batch_text[x],
                        "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_text))
            ]
            
            try:
            _=self.client.upload_records(
                collection_name=collection_name,
                records=batch_record
                )
            return True

        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

        