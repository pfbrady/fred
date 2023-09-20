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