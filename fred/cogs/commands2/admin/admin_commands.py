import discord
from fred import Fred

other_extensions = (
    "cogs.commands2.supervisor.w2w_commands",
    "cogs.commands2.supervisor.formstack_commands",
    "cogs.tasks2.fred_tasks"
)

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name: str, description: str, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    @discord.app_commands.command(description="chems")
    @discord.app_commands.describe(pool="Specific pool location. Options are listed above.")
    async def unload_commands(self, interaction:discord.Interaction):
        for extension in other_extensions:
            self.fred.unload_extension(extension)
        await interaction.response.send_message("All commands unloaded.", ephemeral=True)

async def setup(fred: Fred):
    fred.tree.add_command(Formstack_Commands(name="admin", description="test", fred=fred))