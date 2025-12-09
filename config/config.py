import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    user: str
    password: str
    database: str
    host: str
    port: str

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class BotConfig:
    token: str
    admin_ids: list[int]


@dataclass
class Settings:
    bot: BotConfig
    db: DatabaseConfig


def load_config() -> Settings:
    return Settings(
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN"),
            admin_ids=list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
        ),

        db=DatabaseConfig(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
        )
    )
