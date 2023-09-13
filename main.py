import settings
import discord
import requests
from discord.ext import commands
import datetime
import time


def run():
    while True:
        #intents = discord.Intents.default()

        #req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key=' + settings.W2W_TOKEN)
        #req_json = req.json()

        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=14) #2 weeks from now.

        today = today.strftime("%m/%d/%Y")
        end_date = end_date.strftime("%m/%d/%Y")

        req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date=' + 
                        today + '&end_date=' + end_date + '&key=' + settings.W2W_TOKEN)
                            
        req_json = req.json() 
        print (req_json['AssignedShiftList'])

        '''''
        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(bot.user)

        bot.run(settings.DISCORD_TOKEN)
        '''''

        # 5 seconds sleep
        time.sleep(5)
        print("---------------------------------------------------------------------------------")
        print("----------------------------Sleeping for 5 seconds...----------------------------")

if __name__ == "__main__":
    run()