import abc
from typing import Iterable, Any, Optional, Protocol, List, Tuple


# This is to allow type hinting to work as expected given the cursor classes we use don't have a common ancestor
class CursorExecuteResult(Protocol):
    def fetchall(self) -> List[Tuple]: ...

    def fetchmany(self, size: int) -> List[Tuple]: ...

    def fetchone(self) -> Optional[Tuple]: ...

    def fetchval(self) -> Any: ...

    def __iter__(self) -> 'CursorExecuteResult': ...

    def __next__(self) -> Tuple: ...


class Connection(abc.ABC):
    @abc.abstractmethod
    def execute(self, sql, *params) -> CursorExecuteResult:
        """
        Execute a single SQL statement with bound parameters

        :param sql: The sql statement to execute
        :param params: The parameters to bind to that SQL statement
        :return: The cursor object to allow chaining
        """
        pass

    @abc.abstractmethod
    def executemany(self, sql, params: Iterable[Any]) -> None:
        """
        Execute a single SQL statement across a list of bound parameters. The statement will execute once per element in
        params.

        :param sql: The sql statement to execute multiple times
        :param params: The list of parameters to bind to that SQL statement
        """
        pass

    @property
    @abc.abstractmethod
    def last_row_id(self) -> Optional[int]:
        """
        :return: The last id that was inserted
        """
        pass

    @abc.abstractmethod
    def __enter__(self) -> 'Connection':
        """
        :return: A copy of this connection with a new cursor
        """
        pass

    def __exit__(self, exc_type, exc_val, exc_tb): ...
