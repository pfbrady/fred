from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Dict
from whentowork import Shift, Position, Client
import logging

if TYPE_CHECKING:
    from .types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)

class YMCAW2WClient(Client):
    def __init__(self, hostname:str, token: str, position_ids: YMCAW2WClientPayload):
        super().__init__(hostname, token, logger=log)
        self._update_w2w_position_ids(position_ids)

    def _update_w2w_position_ids(self, position_ids: YMCAW2WClientPayload):
        self.director_id: int = position_ids['director']
        self.specialist_id: int = position_ids['specialist']
        self.supervisor_id: int = position_ids['supervisor']
    
    def filter_shifts(self, shifts: List[Shift], dt_start: datetime = None, dt_end: datetime = None, positions: List[Position] = None):
        if positions:
            shifts = list(filter(lambda shift: shift.position in positions, shifts))           
        if dt_start and dt_end:
            shifts = list(filter(lambda shift: (shift.start_datetime < dt_end and shift.end_datetime > dt_start), shifts))
        return shifts
    
    def sort_shifts_by_date(self, shifts: List[Shift]) -> Dict[datetime.date, List[Shift]]:
        shifts_dict: Dict[datetime.date, List[Shift]] = {}
        for shift in shifts:
            shift_start_date = shift.start_datetime.date()
            if shift_start_date in shifts_dict:
                shifts_dict[shift_start_date] = [shift]
            else:
                shifts_dict[shift_start_date].append(shift)
        return shifts_dict
    
    def get_shifts_now(self, positions: List[Position]):
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, now, now, positions)
    
    def unique_employees(self, shifts: List[Shift]):
        unique_employees = []
        for shift in shifts:
            if shift.employee not in unique_employees:
                unique_employees.append(shift.employee)
        return unique_employees
