from asyncio import current_task

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, async_scoped_session

from effective_mobile_fast_api.core.config import settings


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,  # Подготовка к комиту
            expire_on_commit=False
        )

    # Вспомогательная для scoped_session_dependency
    def get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task
        )
        return session

    async def session_dependency(self):
        async with self.session_factory() as session:
            yield session
            await session.close()

    # Дает 1 сессию на все запросы функции, может экономить ресурсы, если много вызовов сессий
    async def scoped_session_dependency(self):
        session = self.get_scoped_session()
        yield session
        await session.close()


db_helper = DataBaseHelper(
    url=settings.db_url,
    echo=settings.db_echo
)
