import abc

from card_automation_server.plugins.types import CardScan
from card_automation_server.windsx.lookup.access_card import AccessCard


class Plugin(abc.ABC):
    """
    Common base class. If a consumer implements one of the below plugin classes, they implement this class. That makes
    it easier for the framework to just find any plugin class.
    """
    pass


class PluginStartup(Plugin):
    @abc.abstractmethod
    def startup(self) -> None:
        """
        This method will always be called whenever a plugin worker is started, before any other methods.
        """
        pass


class PluginShutdown(Plugin):
    @abc.abstractmethod
    def shutdown(self) -> None:
        """
        This method will be called when the plugin worker is shutting down. This is "best effort" only, there are no
        guarantees.
        """
        pass


class PluginCardScanned(Plugin):
    @abc.abstractmethod
    def card_scanned(self, scan_data: CardScan) -> None:
        """
        Whenever a card is scanned, this method is called.

        :param scan_data: CardScan The card scan data
        """
        pass


class PluginCardDataPushed(Plugin):
    @abc.abstractmethod
    def card_data_pushed(self, access_card: AccessCard) -> None:
        """
        Whenever an access card data is pushed to the physical hardware, this method is called.

        :param access_card: AccessCard The access card that was successfully pushed to the hardware.
        """
        pass


class PluginLoop(Plugin):
    @abc.abstractmethod
    def loop(self) -> int:
        """
        This method allows a plugin to run something on some frequency basis, without having to maintain their own
        threads and making sure they shut down properly. Returning nothing or a value <= 0 just means "run it next loop"
        which is approximately once every second.

        :return how many seconds until this method should be called again.
        """
        pass


# TODO Plugin AcsDatabaseUpdated
# TODO Plugin LogDatabaseUpdated