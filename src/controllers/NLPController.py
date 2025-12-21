from .BaseController import BaseController
from models.DBSchemas.Project import Project
from models.DBSchemas.DataChunk import DataChunk
from stores.LLM import DocumentTypeEnum
import json
from stores.LLM.templates import template_parser

class NLPController(BaseController):
    def __init__(self,vectordb_client,embedding_client,generation_client,template_parser:template_parser):
        super().__init__()
        self.vectordb_client=vectordb_client
        self.embedding_client=embedding_client
        self.generation_client=generation_client
        self.template_parser=template_parser

    def create_collection_name(self,project_id:str):
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self,project:Project):
        collection_name=self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self,project:Project):
        collection_name=self.create_collection_name(project_id=project.project_id)
        collection_info=self.vectordb_client.get_collection_info(collection_name=collection_name)
        #collection info is not serializable so we need to convert it to json
        collection_info=json.loads( 
            #dumps convert to string to be converted to json
            #default=lambda x:x.__dict__ is used to convert the object to dictionary if its not serializable and supported by x library
            json.dumps(collection_info,default=lambda x:x.__dict__)  
        )
        return collection_info

    def index_into_vector_db(self,project:Project,chunks:list[DataChunk],
                                chunk_ids:list[int],do_reset:bool=False):
        #get collection name
        collection_name=self.create_collection_name(project_id=project.project_id)

        #manage items
        texts=[chunk.chunk_text for chunk in chunks]
        metadata=[chunk.chunk_metadata for chunk in chunks]
        vectors=[
            self.embedding_client.embed_text(text=text,document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]
        
        #create collection

        _=self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )
        #insert into vector db
        _= self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=chunk_ids
        )
        return True
        
    def search_vector_db_collection(self,project: Project, text: str, limit: int = 5):

        #collection name
        collection_name=self.create_collection_name(project_id=project.project_id)
        #embed vector
        vector=self.embedding_client.embed_text(
            text=text,
            document_type=DocumentTypeEnum.QUERY.value
        )
        if not vector:
            return False
        #semantic search
        results=self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit
        )

        if not results:
            return False
        
        return results

    
    def answer_rag_questions(self,project:Project,query:str,limit:int=5):
        answer,prompt,chat_history=None,None,None

        #step 1 retrive documents
        retrieved_documents =self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit
        )
        if not retrieved_documents:
            return answer,prompt,chat_history

        # step2: Construct LLM prompt
        system_prompt = self.template_parser.get(
            group="rag",
            key="system_prompt"
        )

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": doc.text,
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt =self.template_parser.get(
            group="rag",
            key="footer_prompt"
        )

         # step3: Construct Generation Client Prompts
        chat_history=[
            self.generation_client.construct_prompt(
                role=self.generation_client.enums.SYSTEM.value,
                prompt=system_prompt
            )]

        full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history
        
