import settings
import requests
import datetime


def run():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1) #next day.

    #today = today.strftime("%m/%d/%Y")
    tomorrow = tomorrow.strftime("%m/%d/%Y")

    req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/DailyPositionTotals?start_date=' + 
                    tomorrow + '&end_date=' + tomorrow + '&key=' + settings.W2W_TOKEN)
    
    req_json = req.json() 
    #print(req_json['DailyPositionTotals'])
    lifeguard_data = [item for item in req_json['DailyPositionTotals'] if item.get('POSITION_NAME', '').lower().find('lifeguard') != -1]

    print(lifeguard_data)
    print("=================================")

    for data in lifeguard_data:
        print(f"There are {data['UNASSIGNED_SHIFTS']} UNASSIGNED lifeguard shifts tomorrow")
        print(f"There are {data['ASSIGNED_SHIFTS']} ASSIGNED_SHIFTS lifeguard shifts tomorrow.")


if __name__ == "__main__":
    run()