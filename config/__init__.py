import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = os.getenv("DB_PORT")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_API_NAME: str = os.getenv("OPENAI_API_NAME")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE")

    # 数据库连接字符串 property表示是一个只读属性，不能修改
    @property
    def DB_URL(self):
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset-utf8m64"
