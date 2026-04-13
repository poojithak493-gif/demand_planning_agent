from pydantic_settings import BaseSettings
from falkordb import FalkorDB


class FalkorSettings(BaseSettings):
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_GRAPH_NAME: str = "demand_graph"

    class Config:
        env_file = ".env"


settings = FalkorSettings()

db = FalkorDB(host=settings.FALKORDB_HOST, port=settings.FALKORDB_PORT)
graph = db.select_graph(settings.FALKORDB_GRAPH_NAME)