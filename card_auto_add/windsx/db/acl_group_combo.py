from itertools import groupby
from typing import Optional, Union, Iterable, Dict, Collection

from card_auto_add.windsx.db.connection.connection import Connection

StringOrFrozenSet = Union[str, frozenset[str], Iterable[str]]


class _AclGroupNameNotFound(Exception):
    def __init__(self, message: str, name: str):
        super().__init__(message)
        self._missing_name = name

    @property
    def missing_name(self) -> str:
        return self._missing_name


class AclGroupNameNotInCombo(_AclGroupNameNotFound):
    def __init__(self, name: str):
        super().__init__(f"\"{name}\" was not found in this Acl Group Combo", name)


class AclGroupNameNotInDatabase(_AclGroupNameNotFound):
    def __init__(self, name: str):
        super().__init__(f"\"{name}\" was not found in the database", name)


class AclGroupCombo:
    def __init__(self,
                 connection: Connection,
                 location_group_id: int,
                 combo_id: int
                 ):
        self._location_group_id = location_group_id
        self._connection = connection
        self._combo_id = combo_id
        self._names: Optional[frozenset[[str]]] = None
        self._in_db: Optional[bool] = None

    @property
    def id(self) -> int:
        return self._combo_id

    @property
    def names(self) -> frozenset[str]:
        if self._names is None:
            self._populate_from_db()

        return self._names

    @property
    def in_db(self) -> bool:
        if self._in_db is None:
            self._populate_from_db()

        return self._in_db

    def __str__(self):
        names = ", ".join(self.names)
        return f"{self.id}: {names}"

    def _populate_from_db(self):
        name_id_rows = self._connection.execute(
            "SELECT AclGrpNameID FROM AclGrpCombo WHERE ComboID = ?",
            self._combo_id
        ).fetchall()

        if len(name_id_rows) == 0:
            self._names = frozenset()
            self._in_db = False
            return

        # We know it's in there now
        self._in_db = True

        # Let's grab our names
        name_ids = set(row[0] for row in name_id_rows)
        id_to_names = self._names_by_id(name_ids)

        self._names = frozenset(id_to_names.values())

    @staticmethod
    def _to_set(*values: StringOrFrozenSet) -> frozenset[str]:
        result = frozenset()

        for value in values:
            if isinstance(value, str):
                result = result.union(frozenset({value}))
            elif isinstance(value, Iterable):
                result = result.union(frozenset(value))
            else:
                result = result.union(value)

        return result

    def _names_by_id(self, name_ids: Collection[int]) -> Dict[int, str]:
        values_question_marks = ', '.join('?' for _ in range(len(name_ids)))
        acl_group_name_rows = self._connection.execute(
            f"SELECT ID, NAME FROM AclGrpName WHERE ID IN ({values_question_marks})",
            *name_ids
        ).fetchall()

        id_to_names = {}

        for row in acl_group_name_rows:
            id_to_names[row[0]] = row[1]

        if len(id_to_names) != len(name_ids):
            raise Exception("Could not fetch all names by ID, suggesting DB has invalid data")

        return id_to_names

    def _name_ids_by_name(self, names: Collection[str]) -> Dict[str, int]:
        values_question_marks = ', '.join('?' for _ in range(len(names)))
        acl_group_name_rows = self._connection.execute(
            f"SELECT ID, NAME FROM AclGrpName WHERE NAME IN ({values_question_marks})",
            *names
        ).fetchall()

        names_to_ids = {}

        for row in acl_group_name_rows:
            names_to_ids[row[1]] = row[0]

        if len(names) != len(names_to_ids):  # Something doesn't match up here, meaning we're missing a name
            for name in names:
                if name not in names_to_ids:
                    raise AclGroupNameNotInDatabase(name)

        return names_to_ids

    def with_names(self, *names: StringOrFrozenSet) -> 'AclGroupCombo':
        names = self._to_set(*names)
        all_names = self.names.union(names)

        return self._get_acl_by_names(all_names)

    def without_names(self, *names: StringOrFrozenSet) -> 'AclGroupCombo':
        names = self._to_set(names)

        for name in names:
            if name not in self.names:
                raise AclGroupNameNotInCombo(name)

        new_names = self.names.difference(names)

        return self._get_acl_by_names(new_names)

    def _get_acl_by_names(self, all_names):
        wanted_name_ids = set(self._name_ids_by_name(all_names).values())

        acl_combos = list(self._connection.execute("SELECT AclGrpNameID, ComboID FROM AclGrpCombo"))
        grouped_by_combo_id = groupby(acl_combos, lambda x: x[1])  # Group by the Combo ID

        for new_combo_id, value in grouped_by_combo_id:
            acl_name_ids = set([x[0] for x in value])
            if acl_name_ids == wanted_name_ids:  # Oh good, we found an exact match
                return AclGroupCombo(
                    self._connection,
                    self._location_group_id,
                    new_combo_id
                )

        # This doesn't exist, so we create one, update the names manually, and mark it as not in the database
        result = AclGroupCombo(self._connection, self._location_group_id, 0)
        result._names = all_names
        result._in_db = False

        return result

    def write(self):
        if self.in_db:
            return

        if len(self._names) == 0:
            return

        names_to_ids = self._name_ids_by_name(self._names)
        name_id_iterator = iter(names_to_ids.values())

        # We need to insert one of them to get a new combo id. The ID field gets a generated ID, which we treat as the
        # combo id for this AclGrpComboId
        with self._connection as conn:  # Scope a new cursor to avoid other cursors messing up our last row id
            conn.execute(
                "INSERT INTO AclGrpCombo(AclGrpNameID, ComboID, LocGrp) VALUES (?, ?, ?)",
                next(name_id_iterator), 0, self._location_group_id
            )
            self._combo_id = conn.last_row_id

        # That insert did not populate ComboID, which means it's currently 0. We update that row to have the same
        # combo_id as its ID
        self._connection.execute(
            "UPDATE AclGrpCombo SET ComboID = ? WHERE ID = ?",
            self._combo_id, self._combo_id
        )

        # Now we just have to insert the rest of our rows
        self._connection.executemany(
            "INSERT INTO AclGrpCombo(AclGrpNameID, ComboID, LocGrp) VALUES (?, ?, ?)",
            [(name_id, self._combo_id, self._location_group_id) for name_id in name_id_iterator]
        )

        self._in_db = True  # Now we're in the database :)
