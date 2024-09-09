import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.engine_factory import EngineFactory
from card_auto_add.windsx.db.models import *

location_group_id = 3
main_location_id = 3
annex_location_id = 4

"""
The table data is relatively hard coded to be used in the tests, but it's useful to explain the overall decisions.
Instead of just dumping the full tables with all of the data, we do filter the table columns down based on what might
be useful. Columns we'll never use in our application aren't included as a general rule.

- There is only one location named "MBD" for "Main Building".
- There are two main time zones.
- There are 3 tenants: 1, 2, and 3.
- There are 5 doors:
 - Main Door (entry to the building common to all tenants)
 - Tenant 1 door
 - Tenant 2 door
 - Tenant 3 door A
 - Tenant 3 door B
"""


def table_location_group(session: Session):
    session.add_all([
        LocGrp(ID=1, LocGrp=location_group_id, Name="MBD")
    ])


def table_location(session: Session):
    session.add_all([
        LOC(
            ID=1,
            Loc=main_location_id,
            LocGrp=location_group_id,
            Name="MBD",
            Status=True,
            PlFlag=False,
            FullDlFlag=False,
            LoFlag=False,
            DlFlag=0
        ),
    ])


def table_timezone(session: Session):
    session.add_all([
        TZ(ID=-659436830,
           Loc=main_location_id,
           TZ=1,
           Name="Always(24x7)",
           LinkStatus=0,
           SunStart=0,
           SunStop=2400,
           MonStart=0,
           MonStop=2400,
           TueStart=0,
           TueStop=2400,
           WedStart=0,
           WedStop=2400,
           ThuStart=0,
           ThuStop=2400,
           FriStart=0,
           FriStop=2400,
           SatStart=0,
           SatStop=2400,
           Hol1Start=0,
           Hol1Stop=2400,
           Hol2Start=0,
           Hol2Stop=2400,
           Hol3Start=0,
           Hol3Stop=2400,
           DlFlag=0),
        TZ(ID=-1576553029,
           Loc=main_location_id,
           TZ=2,
           Name="Front Door Auto Unlock",
           LinkStatus=1,
           SunStart=1300,
           SunStop=945,
           MonStart=1400,
           MonStop=1100,
           TueStart=1400,
           TueStop=1100,
           WedStart=1400,
           WedStop=1100,
           ThuStart=1400,
           ThuStop=1100,
           FriStart=1400,
           FriStop=1100,
           SatStart=2300,
           SatStop=1930,
           Hol1Start=0,
           Hol1Stop=2400,
           Hol2Start=0,
           Hol2Stop=2400,
           Hol3Start=0,
           Hol3Stop=2400,
           DlFlag=0),
    ])


def table_devices(session: Session):
    session.add_all([
        DEV(ID=0, Loc=main_location_id, Device=0, Name='Main Door'),
        DEV(ID=1, Loc=main_location_id, Device=1, Name='Tenant 1 Door'),
        DEV(ID=2, Loc=main_location_id, Device=2, Name='Tenant 2 Door'),
        DEV(ID=3, Loc=main_location_id, Device=3, Name='Tenant 3 Door A'),
        DEV(ID=4, Loc=main_location_id, Device=4, Name='Tenant 3 Door B'),
    ])


def table_acl_group_name(session: Session):
    session.add_all([
        AclGrpName(ID=1, LocGrp=location_group_id, Name="Master Access Level"),
        AclGrpName(ID=2, LocGrp=location_group_id, Name="Main Building Access"),
        AclGrpName(ID=3, LocGrp=location_group_id, Name="Tenant 1"),
        AclGrpName(ID=4, LocGrp=location_group_id, Name="Tenant 2"),
        AclGrpName(ID=5, LocGrp=location_group_id, Name="Tenant 3"),
    ])


def table_acl_group(session: Session):
    session.add_all([
        AclGrp(ID=1, AclGrpNameID=2, Loc=main_location_id, Dev=0, Tz1=1),  # Main Building Access to Main Door
        AclGrp(ID=2, AclGrpNameID=3, Loc=main_location_id, Dev=0, Tz1=1),  # Tenant 1 Access to Main Door
        AclGrp(ID=3, AclGrpNameID=4, Loc=main_location_id, Dev=0, Tz1=1),  # Tenant 2 Access to Main Door
        AclGrp(ID=4, AclGrpNameID=5, Loc=main_location_id, Dev=0, Tz1=1),  # Tenant 3 Access to Main Door
        AclGrp(ID=5, AclGrpNameID=3, Loc=main_location_id, Dev=1, Tz1=1),  # Tenant 1 Access to Tenant 1 Door
        AclGrp(ID=6, AclGrpNameID=4, Loc=main_location_id, Dev=2, Tz1=1),  # Tenant 2 Access to Tenant 2 Door
        AclGrp(ID=7, AclGrpNameID=5, Loc=main_location_id, Dev=3, Tz1=1),  # Tenant 3 Access to Tenant 3 Door A
        AclGrp(ID=8, AclGrpNameID=5, Loc=main_location_id, Dev=4, Tz1=1),  # Tenant 3 Access to Tenant 3 Door B
    ])


def table_acl_group_combo(session: Session):
    session.add_all([
        AclGrpCombo(ID=100, AclGrpNameID=1, ComboID=100, LocGrp=location_group_id),  # 100: Master Access Level
        AclGrpCombo(ID=101, AclGrpNameID=2, ComboID=101, LocGrp=location_group_id),  # 101: Main Building
        AclGrpCombo(ID=102, AclGrpNameID=2, ComboID=102, LocGrp=location_group_id),  # 102: Main Building
        AclGrpCombo(ID=103, AclGrpNameID=3, ComboID=102, LocGrp=location_group_id),  # 102: Tenant 1
        AclGrpCombo(ID=104, AclGrpNameID=2, ComboID=104, LocGrp=location_group_id),  # 104: Main Building
        AclGrpCombo(ID=105, AclGrpNameID=4, ComboID=104, LocGrp=location_group_id),  # 104: Tenant 2
        AclGrpCombo(ID=106, AclGrpNameID=2, ComboID=106, LocGrp=location_group_id),  # 106: Main Building
        AclGrpCombo(ID=107, AclGrpNameID=5, ComboID=106, LocGrp=location_group_id),  # 106: Tenant 3
        AclGrpCombo(ID=108, AclGrpNameID=3, ComboID=108, LocGrp=location_group_id),  # 102: Tenant 1 Only
        AclGrpCombo(ID=109, AclGrpNameID=4, ComboID=109, LocGrp=location_group_id),  # 104: Tenant 2 Only
        AclGrpCombo(ID=110, AclGrpNameID=5, ComboID=110, LocGrp=location_group_id),  # 106: Tenant 3 Only
    ])


def table_company(session: Session):
    # In practice, the COMPANY.id field is not used. The COMPANY.Company field is used as the ID everywhere in the DB.
    session.add_all([
        COMPANY(ID=11, LocGrp=location_group_id, Company=1, Name="Building Management"),
        COMPANY(ID=12, LocGrp=location_group_id, Company=2, Name="Security Company"),
        COMPANY(ID=13, LocGrp=location_group_id, Company=3, Name="Tenant 1"),
        COMPANY(ID=14, LocGrp=location_group_id, Company=4, Name="Tenant 2"),
        COMPANY(ID=15, LocGrp=location_group_id, Company=5, Name="Tenant 3"),
    ])


def table_names(session: Session):
    session.add_all([
        NAMES(ID=1, LocGrp=location_group_id, FName="BobThe", LName="BuildingManager", Company=1),
        NAMES(ID=2, LocGrp=location_group_id, FName="Fire", LName="Key", Company=1),
        NAMES(ID=3, LocGrp=location_group_id, FName="Ray", LName="Securitay", Company=2),
        NAMES(ID=4, LocGrp=location_group_id, FName="Best", LName="Employee", Company=3),
        NAMES(ID=5, LocGrp=location_group_id, FName="Worst", LName="Employee", Company=3),
        NAMES(ID=6, LocGrp=location_group_id, FName="Best", LName="Employee", Company=4),  # Same name, different company
        NAMES(ID=7, LocGrp=location_group_id, FName="ToBe", LName="Fired", Company=4),
        # Tenant 3 intentionally has no employees listed here so we can insert them in the unit test and just assert on
        # count by company
    ])


# TODO Table CARDS
# TODO Table UdfName
# TODO Table UDF (Needs UdfName)
# TODO Table AclGrpCombo
# TODO Table DGRP
# TODO Table ACL (Needs DGRP)
# TODO Table LocCards (Needs CARDS, ACL)

# TODO OLL
# TODO Table IO
# TODO OllName


@pytest.fixture
def acs_data_engine() -> Engine:
    engine = EngineFactory.in_memory_sqlite()
    AcsDataBase.metadata.create_all(engine)

    session = Session(engine)
    table_location_group(session)
    table_location(session)
    table_timezone(session)
    table_devices(session)
    table_acl_group_name(session)
    table_acl_group_combo(session)
    table_company(session)

    session.commit()

    return engine
