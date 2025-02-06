from pathlib import Path

from sqlalchemy import Engine, create_engine, URL, StaticPool


class EngineFactory:
    @staticmethod
    def in_memory_sqlite() -> Engine:
        return create_engine(
            f"sqlite://",
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )

    @classmethod
    def file_sqlite(cls, db_path: Path) -> Engine:
        return create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool
        )

    @staticmethod
    def microsoft_access(db_path: Path) -> Engine:
        connection_string = (
                r'DRIVER={Microsoft Access Driver (*.mdb)};'
                r"ExtendedAnsiSQL=1;"
                r'DBQ=' + str(db_path) + ";"
        )
        connection_url = URL.create(
            "access+pyodbc",
            query={"odbc_connect": connection_string}
        )
        return create_engine(connection_url)
