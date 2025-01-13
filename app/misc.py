from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import config  # noqa

app = FastAPI(
    servers=[{"url": url} for url in config.SERVER_URLS] or None,
)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
