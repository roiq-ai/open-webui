import logging
import os
import time

import docker
import pytest
from docker import DockerClient
from fastapi.testclient import TestClient
from pytest_docker.plugin import get_docker_ip
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from httpx import AsyncClient, ASGITransport

log = logging.getLogger(__name__)


def get_fast_api_client():
    from main import app

    return app


def get_client():
    with TestClient(get_fast_api_client()) as c:
        return c


class AbstractIntegrationTest:
    BASE_PATH = None
    BASE_URL = "http://test"
    app = get_fast_api_client()
    fast_api_client = AsyncClient(app=get_fast_api_client(), base_url=BASE_URL)

    def create_url(self, path="", query_params=None):
        if self.BASE_PATH is None:
            raise Exception("BASE_PATH is not set")
        parts = self.BASE_PATH.split("/")
        parts = [part.strip() for part in parts if part.strip() != ""]
        path_parts = path.split("/")
        path_parts = [part.strip() for part in path_parts if part.strip() != ""]
        query_parts = ""
        if query_params:
            query_parts = "&".join(
                [f"{key}={value}" for key, value in query_params.items()]
            )
            query_parts = f"?{query_parts}"
        return "/".join(parts + path_parts) + query_parts

    @classmethod
    def setup_class(cls):
        os.environ["TEST"] = True

    async def setup_method(self):
        pass

    @classmethod
    async def teardown_class(cls):
        pass

    async def teardown_method(self):
        pass


class AbstractPostgresTest(AbstractIntegrationTest):
    DOCKER_CONTAINER_NAME = "postgres-test-container-will-get-deleted"
    docker_client: DockerClient

    @classmethod
    def _create_db_url(cls, env_vars_postgres: dict) -> str:
        host = get_docker_ip()
        user = "postgres"
        pw = env_vars_postgres["POSTGRES_PASSWORD"]
        port = 8081
        db = env_vars_postgres["POSTGRES_DB"]
        return f"asyncpg+postgresql://{user}:{pw}@{host}:{port}/{db}"

    @classmethod
    async def setup_class(cls):
        super().setup_class()
        try:
            env_vars_postgres = {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "example",
                "POSTGRES_DB": "openwebui",
            }
            cls.docker_client = docker.from_env()
            cls.docker_client.containers.run(
                "postgres:16.2",
                detach=True,
                environment=env_vars_postgres,
                name=cls.DOCKER_CONTAINER_NAME,
                ports={5432: ("0.0.0.0", 8081)},
                command="postgres -c log_statement=all",
            )
            cls.docker_client.containers.run(
                "chromadb/chroma:latest",
                detach=True,
                environment=env_vars_postgres,
                name=cls.DOCKER_CONTAINER_NAME.replace("postgres", "chroma"),
                ports={9099: ("0.0.0.0", 9099)},
                command="--workers 1 --host 0.0.0.0 --port 9099",
            )
            time.sleep(0.5)

            database_url = cls._create_db_url(env_vars_postgres)
            os.environ["DATABASE_URL"] = database_url
            retries = 10
            db = None
            while retries > 0:
                try:
                    pass

                    db = create_async_engine(database_url, pool_pre_ping=True)
                    db = await db.connect()
                    log.info("postgres is ready!")
                    break
                except Exception as e:
                    log.warning(e)
                    time.sleep(3)
                    retries -= 1

            if db:
                # import must be after setting env!
                cls.fast_api_client = get_fast_api_client()
                await db.close()
            else:
                raise Exception("Could not connect to Postgres")
        except Exception as ex:
            log.error(ex)
            await cls.teardown_class()
            pytest.fail(f"Could not setup test environment: {ex}")

    async def _check_db_connection(self):
        from open_webui.apps.webui.internal.db import Session

        retries = 10
        while retries > 0:
            try:
                await Session.execute(text("SELECT 1"))
                await Session.commit()
                break
            except Exception as e:
                await Session.rollback()
                log.warning(e)
                time.sleep(3)
                retries -= 1

    async def setup_method(self):
        await super().setup_method()
        await self._check_db_connection()

    @classmethod
    async def teardown_class(cls) -> None:
        await super().teardown_class()

    async def teardown_method(self):
        from open_webui.apps.webui.internal.db import Session

        # rollback everything not yet committed
        await Session.commit()

        # truncate all tables
        tables = [
            "auth",
            "chat",
            "chatidtag",
            "document",
            "memory",
            "model",
            "prompt",
            "tag",
            '"user"',
        ]
        for table in tables:
            await Session.execute(text(f"TRUNCATE TABLE {table}"))
        await Session.commit()
