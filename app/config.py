import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./metaverse_exhibition.db")

PROJECT_NAME = "Metaverse Exhibition Backend"
VERSION = "1.0.0"

CORS_ORIGINS = ["*"]
