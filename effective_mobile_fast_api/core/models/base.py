from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import SQLModel


class BaseModel(SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        # Автоматически формируем имя таблицы: имя класса в нижнем регистре + "s"
        return cls.__name__.lower() + "s"
