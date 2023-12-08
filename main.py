import settings
import discord
import logging
import requests
from discord.ext import commands
import get_open_shifts as gos
import pytz
import datetime
import asyncio

est = pytz.timezone('US/Eastern')
current_time = datetime.datetime.now(est)

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)


async def send_unassigned_shifts():
    shifts_tuple = gos.open_shifts()
    shifts_as_int = [int(shift) for shift in shifts_tuple]
    lifeguard_unassigned_shifts, aquatic_lead_unassigned_shifts, swim_instr_unassigned_shifts, swam_unassigned_shifts = shifts_as_int
        
    if current_time.hour == 13 and current_time.minute == 41:
        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name == 'test' and lifeguard_unassigned_shifts != 0:
                    await channel.send(f"Hi, there are ({lifeguard_unassigned_shifts}) unassigned Lifeguard shifts tomorrow.")
                elif channel.name == 'test' and aquatic_lead_unassigned_shifts != 0:
                    await channel.send(f"Hi, there are ({aquatic_lead_unassigned_shifts}) unassigned Supervisor shifts tomorrow.")
                elif channel.name == 'test' and swim_instr_unassigned_shifts != 0:
                    await channel.send(f"Hi, there are ({swim_instr_unassigned_shifts}) unassigned Swim Instructor shifts tomorrow.")
                elif channel.name == 'test' and swam_unassigned_shifts != 0:
                    await channel.send(f"Hi, there are ({swam_unassigned_shifts}) unassigned SWAM  shifts tomorrow.")


class Fred:
    def __init__(self, client):
        self.client = client

    async def tasks(self):
        unassigned_shifts = await send_unassigned_shifts()
        return unassigned_shifts

    async def on_ready(self):
        print(f'Logged in as {self.client.user} (ID: {self.client.user.id})')
        print('------')
        while True:
            await self.tasks()
            await asyncio.sleep(3600)
def run():
    @client.event
    async def on_ready():
        print(client.user)
        # await send_unassigned_shifts()

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

    client.run(token=settings.DISCORD_TOKEN_007, log_handler=handler)




if __name__ == "__main__":
    bot_instance = Fred(client)
    client.loop.create_task(bot_instance.on_ready())
    client.run(settings.DISCORD_TOKEN_007)
