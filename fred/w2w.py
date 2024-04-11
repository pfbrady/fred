from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import TYPE_CHECKING, List, Dict, Optional

from whentowork import Shift, Position, Client, Employee

if TYPE_CHECKING:
    from .types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)


class YMCAW2WClient(Client):
    def __init__(self, hostname: str, token: str, position_ids: YMCAW2WClientPayload):
        super().__init__(hostname, token, logger=log)
        self._update_w2w_positions(position_ids)

    def _update_w2w_positions(self, position_ids: YMCAW2WClientPayload):
        self.director: Optional[Position] = self.get_position_by_id(position_ids['director'])
        self.specialist: Optional[Position] = self.get_position_by_id(position_ids['specialist'])
        self.supervisor: Optional[Position] = self.get_position_by_id(position_ids['supervisor'])
        self.swim_instructor: Optional[Position] = self.get_position_by_id(position_ids["swim_instructor"])
        self.private_swim_instructor: Optional[Position] = self.get_position_by_id(
            position_ids["private_swim_instructor"])
        self.swam: Optional[Position] = self.get_position_by_id(position_ids["swam"])
        self._lifeguards: Optional[List[Position]] = [self.get_position_by_id(v) for v in
                                                      position_ids['lifeguard'].values()]

    @property
    def lifeguard_positions(self) -> List[Position]:
        return [pos for pos in self._lifeguards if pos]

    @property
    def swim_instructor_positions(self) -> List[Position]:
        return [pos for pos in [self.swim_instructor, self.private_swim_instructor, self.swam] if pos]

    @property
    def leadership_positions(self) -> List[Position]:
        return [pos for pos in [self.director, self.specialist, self.supervisor] if pos]

    def get_shifts_now(self, positions: List[Position]) -> List[Shift]:
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, now, now, positions)

    def get_shifts_today(self, positions: List[Position]) -> List[Shift]:
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, datetime(now.year, now.month, now.day),
                                  datetime(now.year, now.month, now.day, 23, 59), positions)

    def get_shifts_tomorrow(self, positions: List[Position]) -> List[Shift]:
        tomorrow = datetime.now() + timedelta(days=1)
        today_shifts = self.get_shifts_by_date(tomorrow.date(), tomorrow.date())
        return self.filter_shifts(today_shifts, datetime(tomorrow.year, tomorrow.month, tomorrow.day),
                                  datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59), positions)

    def get_shifts_later(self, positions: List[Position]) -> List[Shift]:
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, now, datetime(now.year, now.month, now.day, 23, 59), positions)

    def get_shifts_earlier(self, positions: List[Position]) -> List[Shift]:
        now = datetime.now()
        today_shifts = self.get_shifts_by_date(now.date(), now.date())
        return self.filter_shifts(today_shifts, datetime(now.year, now.month, now.day), now, positions)

    def get_shifts(self, date_start: date, date_end: date, positions: List[Position]) -> List[Shift]:
        range_shifts = self.get_shifts_by_date(date_start, date_end)
        return self.filter_shifts(range_shifts, positions=positions)

    def get_shifts_extreme(self, date_start: date, date_end: date, positions: List[Position],
                           opener_flag: bool = True) -> List[Shift]:
        range_shifts = self.get_shifts_by_date(date_start, date_end)
        rs_filtered_to_position = self.filter_shifts(range_shifts, positions=positions)
        rs_filtered_dict = self._sort_shifts_by_date_and_position(rs_filtered_to_position)
        return self._get_extreme_shifts_from_sorted(rs_filtered_dict, opener_flag)

    def shifts_sorted_by_employee(self, dt_start: datetime, dt_end: datetime, positions: List[Position]) -> Dict[
        Employee, List[Shift]]:
        range_shifts = self.get_shifts_by_date(dt_start.date(), dt_end.date())
        rs_filtered_to_position = self.filter_shifts(range_shifts, dt_start, dt_end, positions)
        return self._sort_shifts_by_employee(rs_filtered_to_position)

    def shifts_sorted_by_position(self, dt_start: datetime, dt_end: datetime, positions: List[Position]) -> Dict[
        Position, List[Shift]]:
        range_shifts = self.get_shifts_by_date(dt_start.date(), dt_end.date())
        rs_filtered_to_position = self.filter_shifts(range_shifts, dt_start, dt_end, positions)
        return self._sort_shifts_by_position(rs_filtered_to_position)

    @staticmethod
    def filter_shifts(shifts: List[Shift], dt_start: datetime = None, dt_end: datetime = None,
                      positions: List[Position] = None):
        if positions:
            shifts = list(filter(lambda shift: shift.position in positions, shifts))
        if dt_start and dt_end:
            shifts = list(
                filter(lambda shift: (shift.start_datetime < dt_end and shift.end_datetime > dt_start), shifts))
        return shifts

    def _get_extreme_shifts_from_sorted(self, shifts_dict: Dict[datetime.date, Dict[Position, List[Shift]]],
                                        opener_flag: bool = True):
        final_shifts: List[Shift] = []
        for shift_dict_by_pos in shifts_dict.values():
            for shifts in shift_dict_by_pos.values():
                final_shifts.extend(self._get_shifts_extreme(shifts, opener_flag))
        return final_shifts

    @staticmethod
    def _sort_shifts_by_date_and_position(shifts: List[Shift]) -> Dict[datetime.date, Dict[Position, List[Shift]]]:
        shifts_dict: Dict[datetime.date, Dict[Position, List[Shift]]] = {}
        for shift in shifts:
            shift_start_date = shift.start_datetime.date()
            if shift_start_date in shifts_dict:
                if shift.position in shifts_dict[shift_start_date]:
                    shifts_dict[shift_start_date][shift.position].append(shift)
                else:
                    shifts_dict[shift_start_date][shift.position] = [shift]
            else:
                shifts_dict[shift_start_date] = {shift.position: [shift]}
        return shifts_dict

    @staticmethod
    def _sort_shifts_by_employee(shifts: List[Shift]) -> Dict[Employee, List[Shift]]:
        shifts_dict: Dict[Employee, List[Shift]] = {}
        for shift in shifts:
            if shift.employee in shifts_dict:
                shifts_dict[shift.employee].append(shift)
            else:
                shifts_dict[shift.employee] = [shift]
        return shifts_dict

    @staticmethod
    def _sort_shifts_by_position(shifts: List[Shift]) -> Dict[Position, List[Shift]]:
        shifts_dict: Dict[Position, List[Shift]] = {}
        for shift in shifts:
            if shift.position in shifts_dict:
                shifts_dict[shift.position].append(shift)
            else:
                shifts_dict[shift.position] = [shift]
        return shifts_dict

    @staticmethod
    def _get_shifts_extreme(shifts: List[Shift], opener_flag: bool = True):
        extreme_shifts: List[Shift] = []
        if not shifts:
            return extreme_shifts

        extreme_time: Optional[datetime] = None
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
        unique_employees: List[Employee] = []
        for shift in shifts:
            if shift.employee not in unique_employees:
                unique_employees.append(shift.employee)
        return unique_employees
