from unittest.mock import MagicMock

import pytest

from card_auto_add.windsx.db.acs_data import AcsData
from card_auto_add.windsx.db.connection.sqlite import SqliteConnection


location_group_id = 3
main_location_id = 3
annex_location_id = 4

@pytest.fixture
def in_memory_sqlite():
    return SqliteConnection(':memory:')


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


@pytest.fixture
def table_location_group(in_memory_sqlite: SqliteConnection):
    in_memory_sqlite.execute(
        "CREATE TABLE LocGrp(ID INTEGER PRIMARY KEY, LocGrp, Name)")

    rows = [
        (1, location_group_id, "MBD")
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO LocGrp VALUES({values_question_marks})", rows)


@pytest.fixture
def table_location(in_memory_sqlite: SqliteConnection, table_location_group):
    in_memory_sqlite.execute(
        "CREATE TABLE LOC(ID INTEGER PRIMARY KEY, Loc, LocGrp, Name, Status, PlFlag, FullDlFlag, LoFlag, NodeCs, OGrpCs, HolCs, FacilCs, OllCs, TzCs, AclCs, DGrpCs, CodeCs, DlFlag)"
    )

    rows = [
        (1, main_location_id, location_group_id, "MBD", True, False, False, False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO LOC VALUES({values_question_marks})", rows)


@pytest.fixture
def table_timezone(in_memory_sqlite: SqliteConnection, table_location):
    in_memory_sqlite.execute(
        "CREATE TABLE TZ(ID INTEGER PRIMARY KEY, Loc, TZ, Name, LinkStatus, SunStart, SunStop, MonStart, MonStop, TueStart, TueStop, WedStart, WedStop, ThuStart, ThuStop, FriStart, FriStop, SatStart, SatStop, Hol1Start, Hol1Stop, Hol2Start, Hol2Stop, Hol3Start, Hol3Stop, DlFlag, Notes, CkSum)")

    rows = [
        (-659436830, main_location_id, 1, "Always(24x7)", 0, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, 2400, 0, "", 19202),
        (-1576553029, main_location_id, 2, "Front Door Auto Unlock", 1, 1300, 945, 1400, 1100, 1400, 1100, 1400, 1100, 1400, 1100, 1400, 1100, 2300, 1930, 0, 2400, 0, 2400, 0, 2400, 0, "", 21378),
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO TZ VALUES({values_question_marks})", rows)


@pytest.fixture
def table_devices(in_memory_sqlite: SqliteConnection, table_location_group):
    in_memory_sqlite.execute("CREATE TABLE DEV(ID INTEGER PRIMARY KEY, Loc, Device, Name)")

    rows = [
        (0, main_location_id, 0, 'Main Door'),
        (1, main_location_id, 1, 'Tenant 1 Door'),
        (2, main_location_id, 2, 'Tenant 2 Door'),
        (3, main_location_id, 3, 'Tenant 3 Door A'),
        (4, main_location_id, 4, 'Tenant 3 Door B'),
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO DEV VALUES({values_question_marks})", rows)


@pytest.fixture
def table_acl_group_name(in_memory_sqlite: SqliteConnection, table_location_group):
    in_memory_sqlite.execute("CREATE TABLE AclGrpName(ID INTEGER PRIMARY KEY, LocGrp, Name, Notes, Visitor, IsMaster)")

    rows = [
        (1, location_group_id, "Master Access Level", '', False, True),
        (2, location_group_id, "Main Building Access", '', False, False),
        (3, location_group_id, "Tenant 1", '', False, False),
        (4, location_group_id, "Tenant 2", '', False, False),
        (5, location_group_id, "Tenant 3", '', False, False),
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO AclGrpName VALUES({values_question_marks})", rows)


@pytest.fixture
def table_acl_group(in_memory_sqlite: SqliteConnection, table_acl_group_name, table_location, table_devices,
                    table_timezone):
    in_memory_sqlite.execute("CREATE TABLE AclGrp(ID INTEGER PRIMARY KEY, AclGrpNameID, Loc, Dev, Tz1, Tz2, Tz3, Tz4)")

    rows = [
        (1, 2, main_location_id, 0, 1, 0, 0, 0),  # Main Building Access to Main Door
        (2, 3, main_location_id, 0, 1, 0, 0, 0),  # Tenant 1 Access to Main Door
        (3, 4, main_location_id, 0, 1, 0, 0, 0),  # Tenant 2 Access to Main Door
        (4, 5, main_location_id, 0, 1, 0, 0, 0),  # Tenant 3 Access to Main Door
        (5, 3, main_location_id, 1, 1, 0, 0, 0),  # Tenant 1 Access to Tenant 1 Door
        (6, 4, main_location_id, 2, 1, 0, 0, 0),  # Tenant 2 Access to Tenant 2 Door
        (7, 5, main_location_id, 3, 1, 0, 0, 0),  # Tenant 3 Access to Tenant 3 Door A
        (8, 5, main_location_id, 4, 1, 0, 0, 0),  # Tenant 3 Access to Tenant 3 Door B
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO AclGrp VALUES({values_question_marks})", rows)


@pytest.fixture
def table_acl_group_combo(in_memory_sqlite: SqliteConnection, table_location_group, table_acl_group_name):
    in_memory_sqlite.execute("CREATE TABLE AclGrpCombo(ID INTEGER PRIMARY KEY, AclGrpNameID, ComboID, LocGrp)")

    rows = [
        (100, 1, 100, location_group_id),  # 100: Master Access Level
        (101, 2, 101, location_group_id),  # 101: Main Building
        (102, 2, 102, location_group_id),  # 102: Main Building
        (103, 3, 102, location_group_id),  # 102: Tenant 1
        (104, 2, 104, location_group_id),  # 104: Main Building
        (105, 4, 104, location_group_id),  # 104: Tenant 2
        (106, 2, 106, location_group_id),  # 106: Main Building
        (107, 5, 106, location_group_id),  # 106: Tenant 3
        (108, 3, 108, location_group_id),  # 102: Tenant 1 Only
        (109, 4, 109, location_group_id),  # 104: Tenant 2 Only
        (110, 5, 110, location_group_id),  # 106: Tenant 3 Only
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO AclGrpCombo VALUES({values_question_marks})", rows)


@pytest.fixture
def table_company(in_memory_sqlite: SqliteConnection, table_location_group):
    in_memory_sqlite.execute("CREATE TABLE COMPANY(ID INTEGER PRIMARY KEY, LocGrp, Company, Name)")

    # In practice, the COMPANY.id field is not used. The COMPANY.Company field is used as the ID everywhere in the DB.
    rows = [
        (11, location_group_id, 1, "Building Management"),
        (12, location_group_id, 2, "Security Company"),
        (13, location_group_id, 3, "Tenant 1"),
        (14, location_group_id, 4, "Tenant 2"),
        (15, location_group_id, 5, "Tenant 3"),
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO COMPANY VALUES({values_question_marks})", rows)


@pytest.fixture
def table_names(in_memory_sqlite: SqliteConnection, table_location_group, table_company):
    in_memory_sqlite.execute("CREATE TABLE NAMES(ID INTEGER PRIMARY KEY, LocGrp, FName, LName, Company)")

    rows = [
        (1, location_group_id, "BobThe", "BuildingManager", 1),
        (2, location_group_id, "Fire", "Key", 1),
        (3, location_group_id, "Ray", "Securitay", 2),
        (4, location_group_id, "Best", "Employee", 3),
        (5, location_group_id, "Worst", "Employee", 3),
        (6, location_group_id, "Best", "Employee", 4),  # Same name, different company
        (7, location_group_id, "ToBe", "Fired", 4),
        # Tenant 3 intentionally has no employees listed here so we can insert them in the unit test and just assert on
        # count by company
    ]
    values_question_marks = ', '.join('?' for _ in range(len(rows[0])))
    in_memory_sqlite.executemany(f"INSERT INTO NAMES VALUES({values_question_marks})", rows)


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
def acs_data(
        in_memory_sqlite: SqliteConnection,
        table_acl_group_combo,
        table_acl_group,
        table_names
):
    # Tables that would be generated indirectly are not included, by convention
    return AcsData(in_memory_sqlite, location_group_id)
