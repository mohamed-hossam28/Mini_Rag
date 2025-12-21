from fastapi import FastAPI
from routers import base,data,nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers import get_settings
from stores.LLM import LLMProviderFactory
from stores.VectorDB import VectorDBProviderFactory
from stores.LLM.templates.template_parser import template_parser

app = FastAPI()

async def startup_span():
    settings = get_settings()
    app.mongo_conn=AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client=app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory=LLMProviderFactory(config=settings)
    vectordb_provider_factory=VectorDBProviderFactory(config=settings)
    #generation model
    app.generation_client=llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
    #embedding model
    app.embedding_client=llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                            embedding_size=settings.EMBEDDING_MODEL_SIZE)
    #vector db
    app.vectordb_client=vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    app.vectordb_client.connect()
    #template parser
    app.template_parser=template_parser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )

async def shutdown_span():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()

#creating lifespan
app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
