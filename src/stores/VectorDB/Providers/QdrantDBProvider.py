from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from qdrant_client import QdrantClient,models
from typing import List

class QdrantDBProvider(VectorDBInterface):
    def __init__(self,dp_path:str,distance_method:str):
        self.client=None
        self.dp_path=dp_path
        self.distance_method=None

        self.logger=logging.getLogger(__name__)
        if distance_method==DistanceMethodEnums.COSINE.value:
            self.distance_method=models.Distance.COSINE
        elif distance_method==DistanceMethodEnums.DOT.value:
            self.distance_method=models.Distance.DOT
        else:
            self.logger.error(
                f"Unsupported distance method '{distance_method}' provided. Defaulting to COSINE."
            )
            self.distance_method = models.Distance.COSINE


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
                        id=record_id,
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


    def insert_many(self,collection_name:str,texts:list,vectors:list,
                    metadata:list=None,record_ids:list=None,batch_size:int=50):

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        #if metadata is none then make it a list of none to iterate over it
        if metadata is None:
            metadata=[None]*len(texts)
        
        if record_ids is None:
            record_ids=[None]*len(texts) 

        for i in range(0,len(texts),batch_size):
            batch_end=i+batch_size

            batch_text=texts[i:batch_end]
            batch_vector=vectors[i:batch_end]
            batch_metadata=metadata[i:batch_end]
            batch_record_ids=record_ids[i:batch_end]

            batch_record=[
                models.Record(
                    id=batch_record_ids[x],
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

        