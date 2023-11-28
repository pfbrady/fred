import settings
import requests
import datetime
import time
from typing import List
from enum import Enum
from database import YMCADatabase

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
    req_json = requests.get(f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={start_date}&end_date={end_date}&key={settings.W2W_TOKEN}').json()
    
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

def get_open_close_times_today(positions: [W2WPosition]):
    return get_open_close_times(datetime.datetime.now(), positions)

def get_open_close_times(dt_start: datetime.datetime, positions: [W2WPosition], dt_end: datetime.datetime = None):
    # Handle date parameters: If only one date passed, sets times equal.
    start_date = dt_start.strftime("%m/%d/%Y")
    if dt_end:
        end_date = dt_end.strftime("%m/%d/%Y")
    else:
        end_date = start_date
        dt_end = dt_start

    # GET request to W2W API
    req_json = requests.get(f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={start_date}&end_date={end_date}&key={settings.W2W_TOKEN}').json()

    w2w_shifts = [W2WShift(shift) for shift in req_json['AssignedShiftList'] if int(shift['POSITION_ID']) in positions]
    extreme_times = None
    for w2w_shift in w2w_shifts:
        if not extreme_times:
            extreme_times = [w2w_shift.start_datetime, w2w_shift.end_datetime]
        if w2w_shift.start_datetime < extreme_times[0]:
            extreme_times[0] = w2w_shift.start_datetime
        if w2w_shift.end_datetime > extreme_times[1]:
            extreme_times[1] = w2w_shift.end_datetime
    return tuple(extreme_times)

            
        
    

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
    elif default_time == 'week-openers':
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

#print(get_employees(datetime.datetime(2023, 11, 8, 0, 0), datetime.datetime(2023, 11, 8, 23, 59), positions=W2WPosition.INSTRUCTORS.value))
#print(get_employees(datetime.datetime(2023, 10, 30, 12, 0)))
#print(get_employees_now())

# Function goal: get assigned shifts by date and by role
# create possible list of roles that users can pass in: lifeguards, leads, instructors

def get_assigned_shifts(start_date=None, role=None):
    today = datetime.date.today().strftime("%m/%d/%Y")
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%m/%d/%Y")  # Next day

    start_date = tomorrow if start_date == 'tomorrow' else today if start_date == 'today' else start_date
    end_date = start_date

    api_url_shifts = f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={start_date}&end_date={end_date}&key={settings.W2W_TOKEN}'
    req_json_shifts = requests.get(api_url_shifts).json()['AssignedShiftList']

    lifeguard_data = [item for item in req_json_shifts if item.get('POSITION_NAME', '').lower().find('lifeguard') != -1]
    aquatic_lead_data = [item for item in req_json_shifts if item.get('POSITION_NAME', '').lower().find('lead') != -1]
    swim_instr_data = [item for item in req_json_shifts if 'swim' in item.get('POSITION_NAME', '').lower() or 'swam' in item.get('POSITION_NAME', '').lower()]

    messages = []
    if role == 'instructors':
        for instr in swim_instr_data:
            message = f"First Name: {instr.get('FIRST_NAME', '')} \nLast Name: {instr.get('LAST_NAME', '')} \nRole: {instr.get('POSITION_NAME', '')} \nFrom: {instr.get('START_TIME', '')} to {instr.get('END_TIME', '')} \nJob Description: {instr.get('DESCRIPTION', '')} \n----------------------------\n"
            messages.append(message)
    elif role == 'lifeguards':
        for lifeguard in lifeguard_data:
            message = f"First Name: {lifeguard.get('FIRST_NAME', '')} \nLast Name: {lifeguard.get('LAST_NAME', '')} \nRole: {lifeguard.get('POSITION_NAME', '')} \nFrom: {lifeguard.get('START_TIME', '')} to {lifeguard.get('END_TIME', '')} \nJob Description: {lifeguard.get('DESCRIPTION', '')} \n----------------------------\n"
            messages.append(message)
    elif role == 'leads':
        for lead in aquatic_lead_data:
            message = f"First Name: {lead.get('FIRST_NAME', '')} \nLast Name: {lead.get('LAST_NAME', '')} \nRole: {lead.get('POSITION_NAME', '')} \nFrom: {lead.get('START_TIME', '')} to {lead.get('END_TIME', '')} \nJob Description: {lead.get('DESCRIPTION', '')} \n----------------------------\n"
            messages.append(message)
    else:
        for shift in req_json_shifts:
            message = f"First Name: {shift.get('FIRST_NAME', '')} \nLast Name: {shift.get('LAST_NAME', '')} \nRole: {shift.get('POSITION_NAME', '')} \nFrom: {shift.get('START_TIME', '')} to {shift.get('END_TIME', '')} \nJob Description: {shift.get('DESCRIPTION', '')} \n----------------------------\n"
            messages.append(message)
    
    return '\n'.join(messages)

#print(get_assigned_shifts('10/25/2023', role='lifeguards'))
