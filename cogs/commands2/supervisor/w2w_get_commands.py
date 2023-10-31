import datetime
import discord
from discord.ext import commands, tasks
import w2w
import fred as fr

class W2W_Get_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: fr.Fred = fred

    @discord.app_commands.command()
    async def test(self, interaction:discord.Interaction):
        await interaction.response.send_message(f'hrloo')

    @discord.app_commands.command(description="Test2")
    async def test2(self, interaction:discord.Interaction):
        now_staff = w2w.get_employees_now()
        print(now_staff)
        employees = self.fred.database.select_w2w_users(now_staff)
        employees_formatted = [f'<@{id}>' for id in employees]
        print(f"Unpacked list: {*employees_formatted,}")
        await interaction.response.send_message(f"Here is a list of all of the employees working now: {*employees_formatted,}")

        # @commands.command()
        # async def everyone_tomorrow(self, ctx):
        #     await ctx.send()`

async def setup(Fred):
    Fred.tree.add_command(W2W_Get_Commands(name="w2w", description="test", fred=Fred))
