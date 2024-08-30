from typing import List

from card_auto_add.windsx.db.acl_group_combo import AclGroupCombo, StringOrFrozenSet
from card_auto_add.windsx.db.company import Company
from card_auto_add.windsx.db.connection.connection import Connection


class AclGroupComboDSL:
    def __init__(self, connection: Connection, location_group_id: int):
        self._location_group_id = location_group_id
        self._connection = connection

    def empty(self) -> AclGroupCombo:
        return AclGroupCombo(self._connection, self._location_group_id, 0)

    def by_names(self, *names: StringOrFrozenSet) -> AclGroupCombo:
        return self.empty().with_names(*names)

    def by_id(self, combo_id: int):
        return AclGroupCombo(self._connection, self._location_group_id, combo_id)

    def all(self) -> List[AclGroupCombo]:
        combo_id_rows = self._connection.execute("SELECT DISTINCT ComboID FROM AclGrpCombo").fetchall()

        return [self.by_id(row[0]) for row in combo_id_rows]


class CompanyDSL:
    def __init__(self, connection: Connection, location_group_id: int):
        self._location_group_id = location_group_id
        self._connection = connection

    def by_name(self, name: str) -> Company:
        company_row = self._connection.execute("SELECT Company FROM COMPANY WHERE Name = ?", name).fetchone()
        if company_row is None:
            company = Company(self._connection, self._location_group_id, 0)
            company.name = name
        else:
            company = Company(self._connection, self._location_group_id, company_row[0])

        return company

    def by_id(self, company_id: int):
        return Company(self._connection, self._location_group_id, company_id)


class AcsData:
    def __init__(self, connection: Connection, location_group_id: int):
        self._location_group_id = location_group_id
        self._connection = connection
        self._acl_group_combo_dsl = AclGroupComboDSL(connection, location_group_id)
        self._company_dsl = CompanyDSL(connection, location_group_id)

    @property
    def acl_group_combo(self) -> AclGroupComboDSL:
        return self._acl_group_combo_dsl

    @property
    def company(self) -> CompanyDSL:
        return self._company_dsl
