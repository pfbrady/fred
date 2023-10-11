import settings
import requests
import datetime
import time

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


print(get_assigned_shifts('tomorrow'))