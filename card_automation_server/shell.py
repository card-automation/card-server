from ioc import Resolver

from card_automation_server.__main__ import CardAutomationServer
from card_automation_server.config import Config
from card_automation_server.windsx.engines import AcsEngine, LogEngine
from card_automation_server.windsx.lookup.access_card import AccessCard, AccessCardLookup
from card_automation_server.windsx.lookup.acl_group_combo import AclGroupComboLookup, AclGroupComboSet
from card_automation_server.windsx.lookup.door_lookup import Door, DoorLookup
from card_automation_server.windsx.lookup.holiday import Holiday, HolidayLookup
from card_automation_server.windsx.lookup.person import Person, PersonLookup
from card_automation_server.windsx.lookup.timezone import Timezone, TimezoneLookup
from card_automation_server.windsx.lookup.utils import LookupInfo

# Wires the graph up.
resolver: Resolver = CardAutomationServer().resolver

__all__ = [
    "resolver",
    "Resolver",
    "Config",
    "LookupInfo",
    "AccessCard",
    "AccessCardLookup",
    "AclGroupComboLookup",
    "AclGroupComboSet",
    "Door",
    "DoorLookup",
    "Holiday",
    "HolidayLookup",
    "Person",
    "PersonLookup",
    "Timezone",
    "TimezoneLookup",
    "AcsEngine",
    "LogEngine",
]

print("Card automation server shell. In scope:")
print("  " + ", ".join(__all__))
