from itertools import groupby
from typing import Optional, Union, Iterable, Dict, Collection, List

from sqlalchemy import Engine, select, distinct
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import AclGrpCombo, AclGrpName

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


class AclGroupComboHelper:
    def __init__(self, engine: Engine, location_group_id: int):
        self._location_group_id = location_group_id
        self._engine = engine

    def empty(self) -> 'AclGroupComboSet':
        return AclGroupComboSet(self._engine, self._location_group_id, 0)

    def by_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet':
        return self.empty().with_names(*names)

    def by_id(self, combo_id: int):
        return AclGroupComboSet(self._engine, self._location_group_id, combo_id)

    def all(self) -> List['AclGroupComboSet']:
        session = Session(self._engine)
        combo_id_rows = session.execute(select(distinct(AclGrpCombo.ComboID))).all()

        return [self.by_id(row[0]) for row in combo_id_rows]


class AclGroupComboSet:
    def __init__(self,
                 engine: Engine,
                 location_group_id: int,
                 combo_id: int
                 ):
        self._location_group_id = location_group_id
        self._engine = engine
        self._session = Session(engine)
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
        # noinspection PyTypeChecker
        query = select(AclGrpCombo.AclGrpNameID).where(AclGrpCombo.ComboID == self._combo_id)
        name_id_rows = self._session.execute(query).all()

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
        query = select(AclGrpName.ID, AclGrpName.Name).where(AclGrpName.ID.in_(name_ids))
        acl_group_name_rows = self._session.execute(query).all()

        id_to_names = {}

        for row in acl_group_name_rows:
            id_to_names[row[0]] = row[1]

        if len(id_to_names) != len(name_ids):
            raise Exception("Could not fetch all names by ID, suggesting DB has invalid data")

        return id_to_names

    def _name_ids_by_name(self, names: Collection[str]) -> Dict[str, int]:
        query = select(AclGrpName.ID, AclGrpName.Name).where(AclGrpName.Name.in_(names))
        acl_group_name_rows = self._session.execute(query).all()

        names_to_ids = {}

        for row in acl_group_name_rows:
            names_to_ids[row[1]] = row[0]

        if len(names) != len(names_to_ids):  # Something doesn't match up here, meaning we're missing a name
            for name in names:
                if name not in names_to_ids:
                    raise AclGroupNameNotInDatabase(name)

        return names_to_ids

    def with_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet':
        names = self._to_set(*names)
        all_names = self.names.union(names)

        return self._get_acl_by_names(all_names)

    def without_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet':
        names = self._to_set(names)

        for name in names:
            if name not in self.names:
                raise AclGroupNameNotInCombo(name)

        new_names = self.names.difference(names)

        return self._get_acl_by_names(new_names)

    def _get_acl_by_names(self, all_names):
        wanted_name_ids = set(self._name_ids_by_name(all_names).values())

        query = select(AclGrpCombo.AclGrpNameID, AclGrpCombo.ComboID)
        acl_combos = self._session.execute(query).all()
        grouped_by_combo_id = groupby(acl_combos, lambda x: x[1])  # Group by the Combo ID

        for new_combo_id, value in grouped_by_combo_id:
            acl_name_ids = set([x[0] for x in value])
            if acl_name_ids == wanted_name_ids:  # Oh good, we found an exact match
                return AclGroupComboSet(
                    self._engine,
                    self._location_group_id,
                    new_combo_id
                )

        # This doesn't exist, so we create one, update the names manually, and mark it as not in the database
        result = AclGroupComboSet(self._engine, self._location_group_id, 0)
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
        starting_combo = AclGrpCombo(
            AclGrpNameID=next(name_id_iterator),  # next meaning "just grab the first one". We handle any others below
            ComboID=0,  # Explicitly setting this to 0, will update it after this record is inserted
            LocGrp=self._location_group_id
        )
        self._session.add(starting_combo)
        self._session.commit()

        # Now we should have an ID we can assign to this set and to the starting object, which will get updated next commit
        self._combo_id = starting_combo.ComboID = starting_combo.ID

        self._session.add_all(
            [
                AclGrpCombo(
                    AclGrpNameID=name_id,
                    ComboID=self._combo_id,
                    LocGrp=self._location_group_id
                ) for name_id in name_id_iterator
            ]
        )

        self._session.commit()

        self._in_db = True  # Now we're in the database :)
