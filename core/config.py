from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    
    persist_directory: str = Field(..., env="persist_directory")
    embedding_model: str = Field(..., env="embedding_model")
    chunk_size: int = Field(..., env="chunk_size")
    chunk_overlap: int = Field(..., env="chunk_overlap")
    top_k: int = Field(..., env="top_k")
    rebuild: bool = Field(..., env="rebuild")   
    
    api_key: str = Field(..., env="API_KEY")
    base_url: str = Field(..., env="BASE_URL")
    model_name: str = Field(..., env="MODEL_NAME")
    redis_url: str = Field(..., env="REDIS_URL")
    redis_ttl_seconds: int = Field(3600, env="REDIS_TTL_SECONDS")
    redis_key_prefix: str = Field("Chat_Session", env="REDIS_KEY_PREFIX")


    mongo_url: str = Field(..., env="MONGO_URL")
    max_items: int = Field(20, env="MAX_ITEMS")
    storage_dir: str = Field("Storage", env="STORAGE_DIR")
    
    mongo_db_name: str = Field(..., env="mongo_db_name")
    mongo_collection_name: str = Field(..., env="mongo_collection_name")

    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = False
        

settings = Settings()
