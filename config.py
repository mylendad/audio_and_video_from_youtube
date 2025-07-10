from pydantic import BaseSettings

class Settings(BaseSettings):
    token: str
    admin_chat_id: int
    gdrive_folder_id: str
    database_url: str
    
    class Config:
        env_file = ".env"

config = Settings()