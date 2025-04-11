from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import Mock

from card_automation_server.plugins.types import CardScan, CommServerEventType
from card_automation_server.windsx.lookup.door_lookup import DoorLookup, Door
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.events import DoorStateUpdate, DoorState
from tests.conftest import main_location_id, annex_location_id


# Doors are based on the DEV table. See conftest.py for defined doors.

class TestDoorLookup:
    def test_by_default_all_doors_are_visible(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)

        doors: list[Door] = door_lookup.all()

        assert len(doors) == 8

        door_id_set = set(d.id for d in doors)
        assert door_id_set == set(range(8))

    def test_can_limit_doors_that_lookup_sees(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info, 3, 4, 5, 7)  # Tenant 3 doors

        doors: list[Door] = door_lookup.all()

        assert len(doors) == 4
        door_id_set = set(d.id for d in doors)
        assert door_id_set == {3, 4, 5, 7}

    def test_lookup_door_by_id(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)

        door: Door = door_lookup.by_id(1)

        assert door is not None
        assert door.in_db
        assert door.id == 1
        assert door.name == 'Tenant 1 Door'
        assert door.location_id == main_location_id
        assert door.device_id == 1

    def test_lookup_door_by_id_that_does_not_exist(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)

        door: Door = door_lookup.by_id(9)

        assert door is None

    def test_lookup_door_by_id_that_we_cannot_access(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info, 0)

        door: Door = door_lookup.by_id(1)

        assert door is None

    def test_lookup_by_location_and_device_id(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)

        door: Door = door_lookup.by_device_info(annex_location_id, 2)

        assert door is not None
        assert door.in_db
        assert door.id == 7
        assert door.name == 'Tenant 3 Secret Lab Door'
        assert door.location_id == annex_location_id
        assert door.device_id == 2

    def test_lookup_by_location_and_device_id_that_does_not_exist(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)

        door: Door = door_lookup.by_device_info(annex_location_id, 3)

        assert door is None

    def test_lookup_by_location_and_device_id_that_we_cannot_access(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info, 1)

        door: Door = door_lookup.by_device_info(annex_location_id, 2)

        assert door is None

    def test_lookup_by_card_scan(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info, 3, 4, 5, 7)  # Tenant 3 doors

        door: Optional[Door] = door_lookup.by_card_scan(CardScan(
            name_id=101,
            card_number=3000,
            scan_time=datetime.now(),
            device=3,
            event_type=CommServerEventType.ACCESS_GRANTED,
            location_id=main_location_id
        ))

        assert door is not None
        assert door.device_id == 3
        assert door.location_id == main_location_id

    def test_lookup_by_card_scan_that_we_cannot_access(self, lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info, 3, 4, 5, 7)  # Tenant 3 doors

        door: Optional[Door] = door_lookup.by_card_scan(CardScan(
            name_id=101,
            card_number=3000,
            scan_time=datetime.now(),
            device=1,
            event_type=CommServerEventType.ACCESS_GRANTED,
            location_id=main_location_id
        ))

        assert door is None


class TestDoorStateChanges:
    def test_open_sends_update(self,
                               acs_updated_callback: Mock,
                               lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)
        door: Door = door_lookup.by_id(1)

        acs_updated_callback.assert_not_called()

        door.open()

        acs_updated_callback.assert_called_once_with(DoorStateUpdate(
            location_id=main_location_id,
            door_number=1,
            state=DoorState.OPEN,
            timeout=None
        ))

    def test_open_with_timeout(self,
                               acs_updated_callback: Mock,
                               lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)
        door: Door = door_lookup.by_id(1)

        acs_updated_callback.assert_not_called()

        door.open(timedelta(seconds=5))

        acs_updated_callback.assert_called_once_with(DoorStateUpdate(
            location_id=main_location_id,
            door_number=1,
            state=DoorState.OPEN,
            timeout=timedelta(seconds=5)
        ))

    def test_secure_sends_update(self,
                                 acs_updated_callback: Mock,
                                 lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)
        door: Door = door_lookup.by_id(1)

        acs_updated_callback.assert_not_called()

        door.secure()

        acs_updated_callback.assert_called_once_with(DoorStateUpdate(
            location_id=main_location_id,
            door_number=1,
            state=DoorState.SECURE,
            timeout=None
        ))

    def test_secure_with_timeout(self,
                                 acs_updated_callback: Mock,
                                 lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)
        door: Door = door_lookup.by_id(1)

        acs_updated_callback.assert_not_called()

        door.secure(timedelta(seconds=5))

        acs_updated_callback.assert_called_once_with(DoorStateUpdate(
            location_id=main_location_id,
            door_number=1,
            state=DoorState.SECURE,
            timeout=timedelta(seconds=5)
        ))

    def test_timezone_sends_update(self,
                                   acs_updated_callback: Mock,
                                   lookup_info: LookupInfo):
        door_lookup: DoorLookup = DoorLookup(lookup_info)
        door: Door = door_lookup.by_id(1)

        acs_updated_callback.assert_not_called()

        door.timezone()

        acs_updated_callback.assert_called_once_with(DoorStateUpdate(
            location_id=main_location_id,
            door_number=1,
            state=DoorState.TIMEZONE,
            timeout=None
        ))
