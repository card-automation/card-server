from typing import NewType

from sqlalchemy import Engine

AcsEngine = NewType('AcsEngine', Engine)
LogEngine = NewType('LogEngine', Engine)
