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

    LIFEGUARD_COMPLEX = 342888572
    LIFEGUARD_MAIN_BUILDING = 342888573

    AQUATIC_SUPERVISOR = 342888570
    AQUATIC_SPECIALIST = 758159249


def get_assigned_shifts(date, roles=None):
    pass

def get_assigned_shifts(start_date, end_date=None, roles=None):
    today = datetime.date.today().strftime("%m/%d/%Y")
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%m/%d/%Y")  # Next day

    start_date = tomorrow if start_date == 'tomorrow' else today if start_date == 'today' else start_date
    end_date = start_date if end_date in [None, 'today'] else tomorrow if end_date == 'tomorrow' else end_date

    api_url = f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={start_date}&end_date={end_date}&key={settings.W2W_TOKEN}'
    req_json = requests.get(api_url).json()
    return req_json['AssignedShiftList']

def get_guards(dt: datetime.datetime, location: W2WPosition = None):
    day = dt.strftime("%m/%d/%Y")
    req_json = requests.get(f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={day}&end_date={day}&key={settings.W2W_TOKEN}').json()
    guards = []
    for shift in req_json['AssignedShiftList']:
        w2w_shift = W2WShift(shift)
        if w2w_shift.start_datetime < dt and w2w_shift.end_datetime > dt and (w2w_shift.position_id == W2WPosition.LIFEGUARD_COMPLEX.value or w2w_shift.position_id == W2WPosition.LIFEGUARD_MAIN_BUILDING.value):
            guards.append(w2w_shift.employee_id)
    return guards

def get_guards_now(location: W2WPosition = None):
    today = datetime.date.today().strftime("%m/%d/%Y")
    req_json = requests.get(f'https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date={today}&end_date={today}&key={settings.W2W_TOKEN}').json()
    guards = []
    for shift in req_json['AssignedShiftList']:
        w2w_shift = W2WShift(shift)
        if w2w_shift.start_datetime < datetime.datetime.now() and w2w_shift.end_datetime > datetime.datetime.now() and (w2w_shift.position_id == W2WPosition.LIFEGUARD_COMPLEX.value or w2w_shift.position_id == W2WPosition.LIFEGUARD_MAIN_BUILDING.value):
            guards.append(w2w_shift.employee_id)
    return guards


print(get_guards(datetime.datetime(2023, 10, 30, 12, 0)))