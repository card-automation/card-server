from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CardScanEventType(Enum):
    ACCESS_GRANTED = 8
    DENIED_UNKNOWN_CODE = 174
    DENIED_TIMEZONE_INACTIVE = 175
    DENIED_WRONG_ACCESS_LEVEL = 176


@dataclass(frozen=True)
class CardScan:
    name_id: Optional[int]
    card_number: int
    scan_time: datetime
    device: int
    event_type: CardScanEventType
    location_id: int