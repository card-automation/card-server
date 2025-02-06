import abc

from card_auto_add.windsx.lookup.access_card import AccessCard


class WorkerEvent(abc.ABC):
    pass


class AcsDatabaseUpdated(WorkerEvent):
    pass


class LogDatabaseUpdated(WorkerEvent):
    pass


class AccessCardUpdated(WorkerEvent):
    """
    This event is fired when the access card is updated in the Acs database.
    """

    def __init__(self, access_card: AccessCard):
        self._access_card = access_card

    @property
    def access_card(self) -> AccessCard:
        return self._access_card


class LocCardUpdated(WorkerEvent):
    """
    This event is fired when an LocCard entry is written. A worker listening to just AcsDatabaseUpdated might miss a
    change to the LocCards table, so this allows us to be explicit about what was changed by a plugin.
    """

    def __init__(self,
                 id: int,  # noqa
                 card_id: int,
                 location_id: int):
        self._id = id
        self._card_id = card_id
        self._location_id = location_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def card_id(self) -> int:
        return self._card_id

    @property
    def location_id(self) -> int:
        return self._location_id


class AccessCardPushed(WorkerEvent):
    """
    This event is fired after the card has been written to the hardware.
    """

    def __init__(self, access_card: AccessCard):
        self._access_card = access_card

    @property
    def access_card(self) -> AccessCard:
        return self._access_card
