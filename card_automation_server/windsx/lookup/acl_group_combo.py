from __future__ import annotations

import abc
from itertools import groupby
from typing import Optional, Union, Iterable, Dict, Collection, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import AclGrpCombo, AclGrpName
from card_automation_server.windsx.lookup.utils import LookupInfo

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


class AclGroupComboLookup:
    def __init__(self, lookup_info: LookupInfo):
        self._lookup_info: LookupInfo = lookup_info

    def empty(self) -> 'AclGroupComboSet':
        return _empty_combo_set(self._lookup_info)

    def by_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet':
        return self.empty().with_names(*names)

    def by_id(self, combo_id: int) -> 'AclGroupComboSet':
        with self._lookup_info.new_session() as session:
            rows = session.execute(
                select(AclGrpName.Name)
                .join(AclGrpCombo, AclGrpCombo.AclGrpNameID == AclGrpName.ID)
                .where(AclGrpCombo.ComboID == combo_id)
                .where(AclGrpCombo.LocGrp == self._lookup_info.location_group_id)
                .where(AclGrpName.LocGrp == self._lookup_info.location_group_id)
            ).all()
            if not rows:
                return _empty_combo_set(self._lookup_info)
            names = frozenset(row.Name for row in rows)
            return _existing_combo_set(self._lookup_info, combo_id, names)

    def all(self) -> List['AclGroupComboSet']:
        with self._lookup_info.new_session() as session:
            rows = session.execute(
                select(AclGrpCombo.ComboID, AclGrpName.Name)
                .join(AclGrpName, AclGrpName.ID == AclGrpCombo.AclGrpNameID)
                .where(AclGrpCombo.LocGrp == self._lookup_info.location_group_id)
                .where(AclGrpName.LocGrp == self._lookup_info.location_group_id)
            ).all()

            combos: Dict[int, frozenset[str]] = {}
            for row in rows:
                combo_id, name = row.ComboID, row.Name
                combos[combo_id] = combos.get(combo_id, frozenset()) | {name}

            return [
                _existing_combo_set(self._lookup_info, combo_id, names)
                for combo_id, names in combos.items()
            ]


class AclGroupComboSet(abc.ABC):
    @property
    @abc.abstractmethod
    def id(self) -> Optional[int]: ...

    @property
    @abc.abstractmethod
    def names(self) -> frozenset[str]: ...

    @property
    @abc.abstractmethod
    def in_db(self) -> bool: ...

    @abc.abstractmethod
    def with_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet': ...

    @abc.abstractmethod
    def without_names(self, *names: StringOrFrozenSet) -> 'AclGroupComboSet': ...

    @abc.abstractmethod
    def write(self): ...


class _AclGroupComboSet(AclGroupComboSet):
    def __init__(self,
                 lookup_info: LookupInfo,
                 combo_id: Optional[int],
                 names: frozenset[str]
                 ):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = self._lookup_info.location_group_id
        self._combo_id: Optional[int] = combo_id
        self._names: frozenset[str] = names

    @property
    def id(self) -> Optional[int]:
        return self._combo_id

    @property
    def names(self) -> frozenset[str]:
        return self._names

    @property
    def in_db(self) -> bool:
        return self._combo_id is not None

    def __str__(self):
        names = ", ".join(self.names)
        return f"{self.id}: {names}"

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

    def _name_ids_by_name(self, session: Session, names: Collection[str]) -> Dict[str, int]:
        if len(names) == 0:
            # Our tests would handle the below SQL statement just fine, but Microsoft Access is less happy with it.
            return {}

        acl_group_name_rows = session.execute(
            select(AclGrpName.ID, AclGrpName.Name)
            .where(AclGrpName.Name.in_(names))
            .where(AclGrpName.LocGrp == self._location_group_id)
        ).all()

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

    def _get_acl_by_names(self, all_names: frozenset[str]) -> 'AclGroupComboSet':
        with self._lookup_info.new_session() as session:
            wanted_name_ids = set(self._name_ids_by_name(session, all_names).values())

            acl_combos = session.execute(
                select(AclGrpCombo.AclGrpNameID, AclGrpCombo.ComboID)
                .where(AclGrpCombo.LocGrp == self._location_group_id)
            ).all()
            grouped_by_combo_id = groupby(acl_combos, lambda x: x[1])  # Group by the Combo ID

            for new_combo_id, value in grouped_by_combo_id:
                acl_name_ids = set([x.AclGrpNameID for x in value])
                if acl_name_ids == wanted_name_ids:  # Oh good, we found an exact match
                    return _existing_combo_set(self._lookup_info, new_combo_id, all_names)

        # This doesn't exist, so we create one with the names but mark it as not in the database
        return _AclGroupComboSet(self._lookup_info, None, all_names)

    def write(self):
        if self.in_db:
            return

        if len(self._names) == 0:
            return

        with self._lookup_info.new_session() as session:
            names_to_ids = self._name_ids_by_name(session, self._names)
            name_id_iterator = iter(names_to_ids.values())

            # We need to insert one of them to get a new combo id. The ID field gets a generated ID, which we treat as the
            # combo id for this AclGrpComboId
            starting_combo = AclGrpCombo(
                AclGrpNameID=next(name_id_iterator),  # next meaning "just grab the first one". We handle any others below
                ComboID=0,  # Explicitly setting this to 0, will update it after this record is inserted
                LocGrp=self._location_group_id
            )
            session.add(starting_combo)
            session.commit()

            # Now we should have an ID we can assign to this set and to the starting object, which will get updated next commit
            self._combo_id = starting_combo.ComboID = starting_combo.ID

            session.add_all(
                [
                    AclGrpCombo(
                        AclGrpNameID=name_id,
                        ComboID=self._combo_id,
                        LocGrp=self._location_group_id
                    ) for name_id in name_id_iterator
                ]
            )

            session.commit()

            self._lookup_info.updated_callback(self)


def _empty_combo_set(lookup_info: LookupInfo) -> AclGroupComboSet:
    return _AclGroupComboSet(lookup_info, None, frozenset())


def _existing_combo_set(lookup_info: LookupInfo, combo_id: int, names: frozenset[str]) -> AclGroupComboSet:
    return _AclGroupComboSet(lookup_info, combo_id, names)
