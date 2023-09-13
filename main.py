import settings
import discord
import requests
from discord.ext import commands

def run():
    intents = discord.Intents.default()
    req = requests.get('https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key=' + settings.W2W_TOKEN)
    req_json = req.json()
    print(req_json['EmployeeList'][0])

    bot = commands.Bot(command_prefix="!", intents=intents)

    # stuff
    
    @bot.event
    async def on_ready():
        print(bot.user)

    bot.run(settings.DISCORD_TOKEN)

if __name__ == "__main__":
    run()
