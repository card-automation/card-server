import enum
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Literal


class CommServerMessageType(enum.IntEnum):
    EVENT = 1


class CommServerEventType(enum.IntEnum):
    BROADCAST_DOWNLOAD_COMPLETE = 2
    PARAMETER_LOAD_SUCCESSFUL = 5
    INVALID_LOGIN = 6
    ACCESS_GRANTED = 8
    STARTING_FULL_PARAMETER_LOAD = 10
    CODE_ACTIVATE = 12
    CODE_DEACTIVATE = 13
    MESSAGE_RETRY = 16
    PARAMETER_LOAD_REQUEST = 17
    DEVICE_COMM_RESTORAL = 103
    DEVICE_COMM_LOSS = 104
    SECURE_TZ = 109
    OPEN_TZ = 110
    ALARM = 112
    COMM_SERVER_STARTUP = 113
    RESTORAL = 115
    COMM_SERVER_EXIT = 125
    LOCATION_COMMUNICATION_LOSS = 132
    LOCATION_COMMUNICATION_RESTORAL = 133
    OPR_SET_OUTPUT_SECURE = 137
    OPR_SET_OUTPUT_OPEN = 138
    OPR_SET_OUTPUT_TZ = 139
    CONSECUTIVE_DENIED_EXCEEDED = 167
    DENIED_UNKNOWN_CODE = 174
    DENIED_TIMEZONE_INACTIVE = 175
    DENIED_WRONG_ACCESS_LEVEL = 176
    DENIED_UNKNOWN_FACILITY_CODE = 177
    SLAVE_PARAMETER_REQUEST = 183
    SLAVE_DOWNLOAD_COMPLETE = 184
    DENIED_PARITY_ERROR = 188
    OPR_SET_INPUT_ARM = 200
    OPR_SET_INPUT_TZ = 201
    OPR_SET_INPUT_BYPASS = 202
    OPR_SET_OUTPUT_ACCESS = 205
    ALARM_ACKNOWLEDGE = 206
    OPR_SET_INPUT_ALL_TZ = 215
    ALARM_RESOLUTION = 216
    TZ_CHANGE_OVERRIDDEN = 221
    OPR_SET_OUTPUT_ALL_TIME_ZONE = 222
    OPR_SET_OUTPUT_ALL_OPEN = 223
    SLAVE_CHECKSUM_DISCREPANCY = 252
    OPR_SET_DEVICE_DISABLED = 261
    OPR_SET_DEVICE_TZ = 262
    TEMP_ACL_DEACTIVATED = 273
    VALID_LOGIN = 274
    ASCII_FILE_IMPORTED = 285


DoorOverrideEvent = Literal[
    CommServerEventType.OPR_SET_OUTPUT_SECURE,
    CommServerEventType.OPR_SET_OUTPUT_OPEN,
    CommServerEventType.OPR_SET_OUTPUT_TZ,
    CommServerEventType.OPR_SET_OUTPUT_ALL_OPEN,
    CommServerEventType.OPR_SET_OUTPUT_ALL_TIME_ZONE,
]


@dataclass(frozen=True)
class CardScan:
    name_id: Optional[int]
    card_number: int
    scan_time: datetime
    device: int
    event_type: CommServerEventType
    location_id: int

    def __post_init__(self):
        if isinstance(self.event_type, int):
            raise Exception("Crashing hard to find out where this is an integer.")
