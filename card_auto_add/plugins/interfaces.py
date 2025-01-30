import abc

from card_auto_add.plugins.types import CardScan


class Plugin(abc.ABC):
    """
    Common base class. If a consumer implements one of the below plugin classes, they implement this class. That makes
    it easier for the framework to just find any plugin class.
    """
    pass


class PluginStartup(Plugin):
    @abc.abstractmethod
    def startup(self):
        pass


class PluginShutdown(Plugin):
    @abc.abstractmethod
    def shutdown(self):
        pass


class PluginCardScanned(Plugin):
    @abc.abstractmethod
    def card_scanned(self, scan_data: CardScan):
        """
        Whenever a card is scanned, this method is called for each plugin.

        :param scan_data: CardScan The card scan data
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
