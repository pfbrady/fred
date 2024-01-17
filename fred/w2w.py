from __future__ import annotations

from datetime import datetime, date
from typing import TYPE_CHECKING, List, Dict, Tuple, Union
from whentowork import Shift, Position, Client
from whentowork.types import Shift as ShiftPayload
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

    def get_shifts_now(self, positions: List[Position]):
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, now, now, positions)
    
    def get_shifts_extreme(self, date_start: date, date_end: date, positions: List[Position], opener_flag: bool = True):
        range_shifts = self.get_shifts_by_date(date_start, date_end)
        rs_filtered_to_position = self.filter_shifts(range_shifts, positions=positions)
        rs_filtered_dict = self._sort_shifts_by_date_and_position(rs_filtered_to_position)
        return self._get_shifts_from_sorted(rs_filtered_dict, opener_flag)
    
    def get_shifts(self, date_start: date, date_end: date, positions: List[Position]):
        range_shifts = self.get_shifts_by_date(date_start, date_end)
        rs_filtered_to_position = self.filter_shifts(range_shifts, positions=positions)

        

    
    @staticmethod
    def filter_shifts(shifts: List[Shift], dt_start: datetime = None, dt_end: datetime = None, positions: List[Position] = None):
        if positions:
            shifts = list(filter(lambda shift: shift.position in positions, shifts))           
        if dt_start and dt_end:
            shifts = list(filter(lambda shift: (shift.start_datetime < dt_end and shift.end_datetime > dt_start), shifts))
        return shifts
    
    def _get_shifts_from_sorted(self, shifts_dict: Dict[datetime.date, Dict[Position, List[Shift]]], opener_flag: bool = True):
        final_shifts: List[Shift] = []
        for shift_dict_by_pos in shifts_dict.values():
            for shifts in shift_dict_by_pos.values():
                final_shifts.append(self._get_shifts_extreme(shifts, opener_flag))
        return final_shifts

    
    @staticmethod
    def _sort_shifts_by_date_and_position(shifts: List[Shift]) -> Dict[datetime.date, List[Shift]]:
        shifts_dict: Dict[datetime.date, Dict[Position, List[Shift]]] = {}
        for shift in shifts:
            shift_start_date = shift.start_datetime.date()
            shift_position = shift.position
            if shift_start_date in shifts_dict:
                if shift_position in shifts_dict[shift_start_date]:
                    shifts_dict[shift_start_date][shift_position].append(shift)
                else:
                    shifts_dict[shift_start_date][shift_position] = [shift]
            else:
                shifts_dict[shift_start_date] = {shift_position: [shift]}
        return shifts_dict

    @staticmethod
    def _get_shifts_extreme(shifts: List[Shift], opener_flag: bool = True):
        extreme_shifts: List[Shift] = []
        if not shifts:
            return extreme_shifts

        extreme_time: datetime = None
        for shift in shifts:
            if not extreme_time:
                extreme_time = shift.start_datetime
            if opener_flag:
                if shift.start_datetime < extreme_time:
                    extreme_time = shift.start_datetime
                    extreme_shifts.clear()
                    extreme_shifts.append(shift)
                elif opener_flag and shift.start_datetime == extreme_time:
                    extreme_shifts.append(shift)   
            else:     
                if shift.end_datetime > extreme_time:
                    extreme_time = shift.end_datetime
                    extreme_shifts.clear()
                    extreme_shifts.append(shift)
                elif shift.end_datetime == extreme_time:
                    extreme_shifts.append(shift)

        return extreme_shifts    

    @staticmethod
    def unique_employees(shifts: List[Shift]):
        unique_employees: List[Shift] = []
        for shift in shifts:
            if shift.employee not in unique_employees:
                unique_employees.append(shift.employee)
        return unique_employees
