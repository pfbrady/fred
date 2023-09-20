import settings
import requests
import datetime
import time


def run():
    while True:
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=14) #2 weeks from now.

        today = today.strftime("%m/%d/%Y")
        end_date = end_date.strftime("%m/%d/%Y")

        req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date=' + 
                        today + '&end_date=' + end_date + '&key=' + settings.W2W_TOKEN)
                            
        req_json = req.json() 
        print (req_json['AssignedShiftList'])

        # 5 seconds sleep
        print("---------------------------------------------------------------------------------")
        print("----------------------------Sleeping for 5 seconds...----------------------------")
        
        time.sleep(5)

if __name__ == "__main__":
    run()