from card_automation_server.windsx.lookup.access_card import AccessCardLookup, AccessCard
from card_automation_server.windsx.lookup.acl_group_combo import AclGroupComboLookup, AclGroupComboSet
from card_automation_server.windsx.lookup.person import PersonLookup
from card_automation_server.workers.events import LocCardUpdated, AccessCardUpdated
from card_automation_server.workers.update_callback_watcher import UpdateCallbackWatcher
from tests.conftest import main_location_id


class TestUpdateCallbackWatcher:
    def test_acl_group_combo(self, acl_group_combo_lookup: AclGroupComboLookup):
        update_callback_watcher = UpdateCallbackWatcher()

        assert update_callback_watcher.outbound_queue.qsize() == 0

        callback = update_callback_watcher.acs_updated_callback

        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(106)
        callback(acl_group_combo)

        # No emitted updates
        assert update_callback_watcher.outbound_queue.qsize() == 0

    def test_person(self, person_lookup: PersonLookup):
        update_callback_watcher = UpdateCallbackWatcher()

        assert update_callback_watcher.outbound_queue.qsize() == 0

        callback = update_callback_watcher.acs_updated_callback

        person = person_lookup.by_name('BobThe', 'BuildingManager').find()[0]
        callback(person)

        # No emitted updates
        assert update_callback_watcher.outbound_queue.qsize() == 0

    def test_loc_card_update(self):
        update_callback_watcher = UpdateCallbackWatcher()

        assert update_callback_watcher.outbound_queue.qsize() == 0

        callback = update_callback_watcher.acs_updated_callback

        loc_card_update = LocCardUpdated(id=900, card_id=5, location_id=main_location_id)
        callback(loc_card_update)

        assert update_callback_watcher.outbound_queue.qsize() == 1

        loc_card_updated: LocCardUpdated = update_callback_watcher.outbound_queue.get()
        assert loc_card_updated.id == 900
        assert loc_card_updated.card_id == 5
        assert loc_card_updated.location_id == main_location_id

    def test_access_card(self, access_card_lookup: AccessCardLookup):
        update_callback_watcher = UpdateCallbackWatcher()

        assert update_callback_watcher.outbound_queue.qsize() == 0

        callback = update_callback_watcher.acs_updated_callback

        access_card: AccessCard = access_card_lookup.by_card_number(2002)
        callback(access_card)

        assert update_callback_watcher.outbound_queue.qsize() == 1

        access_card_updated: AccessCardUpdated = update_callback_watcher.outbound_queue.get()
        assert access_card_updated.access_card.id == access_card.id
