from typing import List

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import NAMES, COMPANY, UDF, CARDS


class CardHolder(object):
    def __init__(self,
                 name_id,
                 udf_id,
                 first_name,
                 last_name,
                 company,
                 card,
                 card_active):
        self.name_id = name_id
        self.udf_id = udf_id
        self.first_name = first_name
        self.last_name = last_name
        self.company = company
        self.card = card
        self.card_active = card_active


class WinDSXActiveCardHolders(object):
    def __init__(self, acs_engine: Engine):
        self._acs_engine = acs_engine
        self._session: Session = Session(acs_engine)

    def get_active_card_holders(self, company_name) -> List[CardHolder]:
        rows = self._session.execute(
            select(
                NAMES.ID.label('name_id'),
                NAMES.FName.label('first_name'),
                NAMES.LName.label('last_name'),
                COMPANY.Name.label('company_name'),
                UDF.UdfText.label('udf_id'),
                CARDS.Code.label('card_code'),
                CARDS.Status.label('card_status'),
            )
            .join(COMPANY, NAMES.Company == COMPANY.Company)
            .join(CARDS, CARDS.NameID == NAMES.ID)
            .outerjoin(UDF, UDF.NameID == NAMES.ID)  # Left join
            .where(COMPANY.Name == company_name)
            .where(CARDS.Status)
        ).all()

        card_holders = []
        for row in rows:
            card_holders.append(CardHolder(
                name_id=row.name_id,
                udf_id=row.udf_id,
                first_name=row.first_name,
                last_name=row.last_name,
                company=row.company_name,
                card=str(row.card_code).strip('0').rstrip('.'),
                card_active=row.card_status
            ))

        return card_holders
