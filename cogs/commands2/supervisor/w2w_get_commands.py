import datetime
import discord
from discord.ext import commands, tasks
from w2w import get_assigned_shifts

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred

class W2W_Get_Commands(commands.Cog):

    def __init__(self, Fred):
        self.Fred = Fred
    
    @commands.command()
    async def test(self, ctx, *, member:discord.Member, interaction:discord.Interaction):
        await interaction.response.send_message(f'{member.display_name} joined on {member.joined_at.date()}')

    @commands.command()
    async def test2(self, ctx, interactions:discord.Integration):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1) #next day.
        tomorrow = tomorrow.strftime("%m/%d/%Y")
        tomorrow_staff = get_assigned_shifts(tomorrow)
        await ctx.send(f"Here is a list of all of the employees working tomorrow:")

    # @commands.command()
    # async def everyone_tomorrow(self, ctx):
    #     await ctx.send()

async def setup(fred):
    await fred.add_cog(W2W_Get_Commands(fred))
