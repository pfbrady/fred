import datetime
import discord
from discord.ext import commands, tasks
from w2w import get_assigned_shifts

class W2W_Get_Commands(discord.app_commands.Group):

    @discord.app_commands.command()
    async def test(self, interaction:discord.Interaction):
        await interaction.response.send_message(f'hrloo')

    @discord.app_commands.command(description="Test2")
    async def test2(self, interaction:discord.Integration):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1) #next day.
        tomorrow = tomorrow.strftime("%m/%d/%Y")
        #tomorrow_staff = get_assigned_shifts(tomorrow)
        await interaction.response.sendmessage(f"Here is a list of all of the employees working tomorrow:")

    # @commands.command()
    # async def everyone_tomorrow(self, ctx):
    #     await ctx.send()

async def setup(Fred):
    await Fred.tree.add_command(W2W_Get_Commands(name="w2w-get-commands"))
