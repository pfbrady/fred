import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w
import fred as fr

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: fr.Fred = fred

async def setup(Fred):
    Fred.tree.add_command(Formstack_Commands(name="form", description="test", fred=Fred))