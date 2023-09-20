import settings
import discord
import requests
from discord.ext import commands


def run():
        #req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key=' + settings.W2W_TOKEN)
        #req_json = req.json()
        #print(req_json["EmployeeList"][0])

        intents = discord.Intents.default()
        intents.message_content = True

    intents = discord.Intents.default()
    req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key=' + settings.W2W_TOKEN)
    req_json = req.json()
    print(req_json['EmployeeList'][0])
    req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/AssignedShiftList?start_date=' + '09/09/2023' + '&end_date=' + '09/10/2023' +' &key=' + settings.W2W_TOKEN)
    req_json = req.json()
    print(req_json['AssignedShiftList'][-1])

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            print(bot.user)
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.name == 'test':
                        await channel.send("Yo, I'm your future bot. Call me Fred :)")


        #bot.run(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    run()