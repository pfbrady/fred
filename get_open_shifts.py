import settings
import requests
import datetime


def open_shifts():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1) #next day.

    #today = today.strftime("%m/%d/%Y")
    tomorrow = tomorrow.strftime("%m/%d/%Y")

    req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/DailyPositionTotals?start_date=' + 
                    tomorrow + '&end_date=' + tomorrow + '&key=' + settings.W2W_TOKEN)
    
    req_json = req.json() 
    #print(req_json['DailyPositionTotals'])
    lifeguard_data = [item for item in req_json['DailyPositionTotals'] if item.get('POSITION_NAME', '').lower().find('lifeguard') != -1]
    aquatic_lead_data = [item for item in req_json['DailyPositionTotals'] if item.get('POSITION_NAME', '').lower().find('lead') != -1]
    swim_instr_data = [item for item in req_json['DailyPositionTotals'] if item.get('POSITION_NAME', '').lower().find('swim') != -1]
    swam_data = [item for item in req_json['DailyPositionTotals'] if item.get('POSITION_NAME', '').lower().find('swam') != -1]


    lifeguard_unassigned_shifts = None
    aquatic_lead_unassigned_shifts = None
    swim_instr_unassigned_shifts = None
    swam_unassigned_shifts = None

    for lifeguard, aquatic_lead, swim_instr, swam in zip(lifeguard_data, aquatic_lead_data, swim_instr_data, swam_data):
        lifeguard_unassigned_shifts = lifeguard['UNASSIGNED_SHIFTS']
        aquatic_lead_unassigned_shifts = aquatic_lead['UNASSIGNED_SHIFTS']
        swim_instr_unassigned_shifts = swim_instr['UNASSIGNED_SHIFTS']
        swam_unassigned_shifts = swam['UNASSIGNED_SHIFTS']
        
    return lifeguard_unassigned_shifts, aquatic_lead_unassigned_shifts, swim_instr_unassigned_shifts, swam_unassigned_shifts









