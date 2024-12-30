from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import COMPANY, EvnLog, NAMES, DEV


class CardScan(object):
    def __init__(self,
                 name_id,
                 first_name,
                 last_name,
                 company,
                 card,
                 scan_time,
                 access_allowed,
                 device):
        self.name_id = name_id
        self.first_name = first_name
        self.last_name = last_name
        self.company = company
        self.card = card
        self.scan_time = scan_time
        self.access_allowed = access_allowed
        self.device = device


class WinDSXCardScan(object):
    def __init__(self,
                 acs_engine: Engine,
                 log_engine: Engine,
                 ):
        self._acs_engine: Engine = acs_engine
        self._acs_session: Session = Session(acs_engine)
        self._log_engine: Engine = log_engine
        self._log_session: Session = Session(log_engine)
        self._company: COMPANY = self._get_company_from_name("denhac")  # TODO Don't hardcode

    def get_scan_events_since(self, timestamp):
        access_allowed_code = 8
        access_denied_unknown_code = 174
        # TODO Do we need to support other access denied codes like wrong timezone?
        rows = self._log_session.execute(
            select(
                EvnLog.TimeDate.label('timestamp'),
                EvnLog.Event.label('event'),
                EvnLog.Code.label('card_code'),
                EvnLog.Opr.label('name_id'),
                EvnLog.Dev.label('device')
            )
            .where(EvnLog.Event.in_([access_allowed_code, access_denied_unknown_code]))
            .where(EvnLog.IO == self._company.Company)
            .where(EvnLog.TimeDate > timestamp)
        ).all()

        card_scans = []

        for row in rows:
            name_info = self._get_name_info_from_id(row.name_id)
            if name_info is None:
                # TODO Does this happen? Should we report on it?
                continue  # We couldn't find the name for this event

            access_allowed = row.event == access_allowed_code
            card_scans.append(CardScan(
                name_id=row.name_id,
                first_name=name_info.first_name,
                last_name=name_info.last_name,
                company=name_info.company_name,
                card=str(row.card_code).strip('0').rstrip('.'),
                scan_time=row.timestamp,
                access_allowed=access_allowed,
                device=row.device
            ))

        return card_scans

    def get_devices(self):
        rows = self._acs_session.execute(select(DEV.Device, DEV.Name)).all()

        result = {}
        for row in rows:
            result[row.Device] = row.Name

        return result

    def _get_name_info_from_id(self, name_id):
        name_data = self._acs_session.execute(
            select(
                NAMES.ID.label('name_id'),
                NAMES.FName.label('first_name'),
                NAMES.LName.label('last_name'),
                COMPANY.Name.label('company_name'),
            )
            .join(COMPANY, COMPANY.Company == NAMES.Company)
            .where(NAMES.ID == name_id)
        ).first()

        return name_data

    def _get_company_from_name(self, company_name: str) -> COMPANY:
        return self._acs_session.scalar(select(COMPANY).where(COMPANY.Name == company_name))
