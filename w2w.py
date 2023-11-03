import settings
import requests
import datetime
import time
from enum import Enum

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
            start_time = []
            if 'pm' in shift[f'{prefix}_TIME']:
                if ':' in shift[f'{prefix}_TIME']:
                    start_time = shift[f'{prefix}_TIME'].split(':')
                    start_time[0] = int(start_time[0]) + 12
                    start_time[1] = int(start_time[1][:-2])
                else:
                    start_time.append(int(shift[f'{prefix}_TIME'][:-2]) + 12)
                    start_time.append(0)
            else:
                if ':' in shift[f'{prefix}_TIME']:
                    start_time = shift[f'{prefix}_TIME'].split(':')
                    start_time[0] = int(start_time[0])
                    start_time[1] = int(start_time[1][:-2])
                else:
                    start_time.append(int(shift[f'{prefix}_TIME'][:-2]))
                    start_time.append(0)
            return datetime.datetime(start_date[2], start_date[0], start_date[1], start_time[0], start_time[1])

class W2WPosition(Enum):
    SWAM = 728636793
    SWIM_INSTRUCTOR_WESTERN = 442123622
    INSTRUCTORS = [728636793, 442123622]

    LIFEGUARD_COMPLEX = 342888572
    LIFEGUARD_MAIN_BUILDING = 342888573
    AQUATIC_SUPERVISOR = 342888570
    AQUATIC_SPECIALIST = 758159249
    GUARDS = [342888572, 342888573, 342888570, 758159249]

def get_employees(dt_start: datetime.datetime, dt_end: datetime.datetime = None, positions: [W2WPosition] = None):
    # Handle date parameters: If only one date passed, sets times equal
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

    # Selects guards with shifts that overlap with the indicated date and time
    selected_employees = []
    for shift in req_json['AssignedShiftList']:
        w2w_shift = W2WShift(shift)
        if w2w_shift.start_datetime < dt_end and w2w_shift.end_datetime > dt_start and w2w_shift.position_id in positions and w2w_shift.position_id not in selected_employees:
            selected_employees.append(w2w_shift.employee_id)
    return selected_employees

def get_employees_now(positions: [W2WPosition] = None):
    return get_employees(datetime.datetime.now(), positions=positions)

print(get_employees(datetime.datetime(2023, 10, 30, 12, 0), datetime.datetime(2023, 10, 30, 13, 0)))
print(get_employees(datetime.datetime(2023, 10, 30, 12, 0)))
print(get_employees_now())