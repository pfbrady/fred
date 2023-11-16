import settings
import requests
import datetime

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
