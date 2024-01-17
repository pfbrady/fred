from __future__ import annotations

import settings
import datetime
import time
from typing import TYPE_CHECKING, List
from enum import Enum
import whentowork
import logging
from fred.ymca.database import YMCADatabase

if TYPE_CHECKING:
    from .types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)

class YMCAW2WClient(whentowork.Client):
    def __init__(self, hostname:str, token: str, position_ids: YMCAW2WClientPayload):
        super().__init__(hostname, token, logger=log)
        self._update_w2w_position_ids(position_ids)

    def _update_w2w_position_ids(self, position_ids: YMCAW2WClientPayload):
        self.director_id: int = position_ids['director']
        self.specialist_id: int = position_ids['specialist']
        self.supervisor_id: int = position_ids['supervisor']
    
    def filter_shifts(self, shifts: List[whentowork.Shift], dt_start: datetime.datetime = None, dt_end: datetime.datetime = None, positions: List[whentowork.Position] = None):
        if positions:
            shifts = list(filter(lambda shift: shift.position in positions, shifts))           
        if dt_start and dt_end:
            shifts = list(filter(lambda shift: (shift.start_datetime < dt_end and shift.end_datetime > dt_start), shifts))
        return shifts
    
    def get_shifts_now(self, positions: List[whentowork.Position]):
        now = datetime.datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, now, now, positions)
    
    def unique_employees(self, shifts: List[whentowork.Shift]):
        unique_employees = []
        for shift in shifts:
            if shift.employee not in unique_employees:
                unique_employees.append(shift.employee)
        return unique_employees
