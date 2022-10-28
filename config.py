from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.general import general_router
from routes.sync import sync_router
from routes.states import states_router
from routes.auth import auth_router
from routes.students import students_router
import os

path_data = os.getenv('LOCALAPPDATA')


def create_app() -> FastAPI:
    app = FastAPI()

    origins = [
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_tortoise(
        app,
        db_url=f'sqlite://{path_data}/ims/db.sqlite3',
        modules={'models': ["models.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    register_views(app=app)
    return app


def register_views(app: FastAPI):
    app.include_router(general_router, tags=["General"])
    app.include_router(students_router, tags=["Students"])
    app.include_router(states_router, tags=["States"])
    app.include_router(auth_router, tags=["Auth"])
    app.include_router(sync_router, tags=["Sync"])


TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{path_data}/ims/db.sqlite3"
    },
    "apps": {
        "models": {
            "models": [
                "models.models", "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}
