from __future__ import annotations

import settings
import requests
import datetime
import time
from typing import TYPE_CHECKING, List
from enum import Enum
import whentowork
import logging
from fred.database import YMCADatabase

if TYPE_CHECKING:
    from .types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)

class YMCAW2WClient(whentowork.Client):
    def __init__(self, hostname:str, token: str, position_ids: YMCAW2WClientPayload):
        super().__init__(hostname, token, logger=log)
        self._update_w2w_position_ids(position_ids)

    def _update_w2w_position_ids(self, position_ids: YMCAW2WClientPayload):
        self.director_id = position_ids['director']
        self.specialist_id = position_ids['specialist']
        self.supervisor_id = position_ids['supervisor']

    def filer_by_positions(self, positions: List[whentowork.Position], shift: whentowork.Shift):
        return True if shift.position in positions else False
    
    def filer_by_time(self, shift: whentowork.Shift, dt_start: datetime.datetime, dt_end: datetime.datetime):
        return True if shift.start_datetime < dt_end and shift.end_datetime > dt_start else False
    
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

    


class W2WShift():
    def __init__(self, w2w_api_dict):
        self.employee_id = int(w2w_api_dict['W2W_EMPLOYEE_ID'])
        self.first_name = w2w_api_dict['FIRST_NAME']
        self.last_name = w2w_api_dict['LAST_NAME']
        self.start_date = w2w_api_dict['START_DATE']
        self.start_time = w2w_api_dict['START_TIME']
        self.start_datetime = self.handle_time(w2w_api_dict, prefix='START')
        self.end_date = w2w_api_dict['END_DATE']
        self.end_time = w2w_api_dict['END_TIME']
        self.end_datetime = self.handle_time(w2w_api_dict, prefix='END')
        self.duration = w2w_api_dict['DURATION']
        self.position_id = int(w2w_api_dict['POSITION_ID'])
        self.position_name = w2w_api_dict['POSITION_NAME']
        self.description = w2w_api_dict['DESCRIPTION']
        self.color_id = int(w2w_api_dict['COLOR_ID'])
        

        
    def handle_time(self, shift, prefix):
            start_date = [int(i) for i in shift[f'{prefix}_DATE'].split('/')]
            start_time = shift[f'{prefix}_TIME'].split(':')
            if 'pm' in shift[f'{prefix}_TIME']:
                hour_shift = 0 if '12' in start_time[0] else 12
                if len(start_time) == 2:
                    start_time[0] = int(start_time[0]) + hour_shift
                    start_time[1] = int(start_time[1][:-2])
                else:
                    start_time[0] = (int(shift[f'{prefix}_TIME'][:-2]) + hour_shift)
                    start_time.append(0)
            else:
                if len(start_time) == 2:
                    start_time = shift[f'{prefix}_TIME'].split(':')
                    start_time[0] = int(start_time[0])
                    start_time[1] = int(start_time[1][:-2])
                else:
                    start_time[0] = (int(shift[f'{prefix}_TIME'][:-2]))
                    start_time.append(0)
            #print(f'name: {shift["FIRST_NAME"]} date: {start_date} hour: {start_time[0]} minute {start_time[1]}')
            return datetime.datetime(start_date[2], start_date[0], start_date[1], start_time[0], start_time[1])

class W2WPosition(Enum):
    SWAM = 728636793
    SWIM_INSTRUCTOR_WESTERN = 442123622
    INSTRUCTORS = [SWAM, SWIM_INSTRUCTOR_WESTERN]

    LIFEGUARD_COMPLEX = 342888572
    LIFEGUARD_MAIN_BUILDING = 342888573
    AQUATIC_SUPERVISOR = 342888570
    AQUATIC_SPECIALIST = 758159249
    GUARDS = [LIFEGUARD_COMPLEX, LIFEGUARD_MAIN_BUILDING, AQUATIC_SUPERVISOR, AQUATIC_SPECIALIST]

def get_employees(dt_start: datetime.datetime, dt_end: datetime.datetime = None, positions: [W2WPosition] = None, position_flag: str = None):
    # Handle date parameters: If only one date passed, sets times equal.
    start_date = dt_start.strftime("%m/%d/%Y")
    if dt_end:
        end_date = dt_end.strftime("%m/%d/%Y")
    else:
        end_date = start_date
        dt_end = dt_start

    # GET request to W2W API
    req_json = requests.get(f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={start_date}&end_date={end_date}&key={settings.W2W_TOKEN_007}').json()
    
    # Handle position parameter. If nothing passes in, defaults to all postions.
    if not positions:
        positions = []
        for position in W2WPosition:
            if isinstance(position.value, int):
                positions.append(position.value)

    # Creates shifts dictionary (filtering out non-relevant positions), ordered by date at root level then position_id at depth = 1.
    w2w_shifts_by_date = {}
    for shift in req_json['AssignedShiftList']:
        if int(shift['POSITION_ID']) in positions:
            w2w_shift = W2WShift(shift)
            if w2w_shift.start_date not in w2w_shifts_by_date.keys():
                w2w_shifts_by_date.update({w2w_shift.start_date: {w2w_shift.position_id: [w2w_shift]}})
            elif w2w_shift.position_id not in w2w_shifts_by_date[w2w_shift.start_date].keys():
                w2w_shifts_by_date[w2w_shift.start_date].update({w2w_shift.position_id: [w2w_shift]})
            else:
                w2w_shifts_by_date[w2w_shift.start_date][w2w_shift.position_id].append(w2w_shift)

    # Iterates through shift dictionary, selecting employees if their shift overlaps the passed in date/time range. If applicable,
    # selects ONLY the extreme (i.e. closers or openers) shifts by day and position.
    selected_employees = []
    for date in w2w_shifts_by_date.values():
        for date_pos in date.values():
            extreme_time = None
            sel_emp_temp = []
            for w2w_shift in date_pos:
                if not position_flag:
                    if w2w_shift.start_datetime < dt_end and w2w_shift.end_datetime > dt_start and w2w_shift.employee_id not in sel_emp_temp:
                        sel_emp_temp.append(w2w_shift.employee_id)
                else:
                    if not extreme_time:
                        extreme_time = w2w_shift.start_datetime
                    if position_flag == 'openers' and w2w_shift.start_datetime < extreme_time:
                        extreme_time = w2w_shift.start_datetime
                        sel_emp_temp.clear()
                        sel_emp_temp.append(w2w_shift.employee_id)
                    elif position_flag == 'openers' and w2w_shift.start_datetime == extreme_time:
                        sel_emp_temp.append(w2w_shift.employee_id)        
                    elif position_flag == 'closers' and w2w_shift.end_datetime > extreme_time:
                        extreme_time = w2w_shift.end_datetime
                        sel_emp_temp.clear()
                        sel_emp_temp.append(w2w_shift.employee_id)
                    elif position_flag == 'closers' and w2w_shift.end_datetime == extreme_time:
                        sel_emp_temp.append(w2w_shift.employee_id)
            for emp in sel_emp_temp:
                if emp not in selected_employees:
                    selected_employees.append(emp)
    
    return selected_employees

            
        
    

def get_employees_now(positions: [W2WPosition] = None):
    return get_employees(datetime.datetime.now(), positions=positions)

def w2wpos_from_default_pos(default_pos:str, type:W2WPosition):
    if default_pos == 'all':
        return type.value
    elif type == W2WPosition.GUARDS:
        if default_pos == 'complex':
            return [type.value[0], type.value[2]]
        else:
            return [type.value[1], type.value[2]]
    else: # if type is instructors
        if default_pos == 'group':
            return [type.value[1]]
        else:
            return [type.value[0]] # SWAM
        
def w2w_from_default_time(default_time: str, positions: [W2WPosition] = None):
    now = datetime.datetime.now()
    if default_time == 'now':
        return get_employees_now(positions)
    elif default_time == 'earlier-today':
        return get_employees(datetime.datetime(now.year, now.month, now.day), now, positions)
    elif default_time == 'later-today':
        return get_employees(now, datetime.datetime(now.year, now.month, now.day, 23, 59), positions)
    elif default_time == 'today':
        return get_employees(datetime.datetime(now.year, now.month, now.day), datetime.datetime(now.year, now.month, now.day, 23, 59), positions)
    elif default_time == 'tomorrow':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
            positions
        )
    elif default_time == 'week':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
            positions
        )
    elif default_time == 'today-closers':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day, 19, 59), 
            datetime.datetime(now.year, now.month, now.day, 23, 59), 
            positions,
            'closers'
        )
    elif default_time == 'tomorrow-openers':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
            positions,
            'openers'
        )
    elif default_time == 'tomorrow-closers':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
            positions,
            'closers'
        )
    elif default_time == 'week-openers':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
            positions,
            'openers'
        )
    elif default_time == 'week-closers':
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
            positions,
            'closers'
        )
    else:
        weekdays = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        today = datetime.datetime(now.year, now.month, now.day).weekday()
        delta = weekdays[default_time] - today
        if delta <= 0:
            delta += 7
        return get_employees(
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=delta), 
            datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=delta, hours=23, minutes=59), 
            positions
        )

