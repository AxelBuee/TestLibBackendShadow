import os
from functools import lru_cache


class Settings:
    def __init__(self):
        self.auth0_domain: str = os.getenv("AUTH0_DOMAIN")
        self.auth0_api_audience: str = os.getenv("AUTH0_API_AUDIENCE")
        self.auth0_issuer: str = os.getenv("AUTH0_ISSUER")
        self.auth0_algorithms: str = os.getenv("AUTH0_ALGORITHMS")
        self.client_id: str = os.getenv("CLIENT_ID")
        self.client_secret: str = os.getenv("CLIENT_SECRET")


class Db_Settings:
    def __init__(self):
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_host = os.getenv("POSTGRES_HOST")
        self.db_port = "5432"
        self.db_name = os.getenv("POSTGRES_DB")

    def get_db_uri(self):
        uri = (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return uri


@lru_cache()
def get_settings():
    return Settings()
