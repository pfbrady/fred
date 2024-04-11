import logging

import discord
import discord.ext.commands

from fred import Fred

other_extensions = (
    "fred.cogs.commands2.supervisor.w2w_commands",
    "fred.cogs.commands2.supervisor.formstack_commands",
    "fred.cogs.commands2.public.schedule_commands"
)


class FormstackCommands(discord.app_commands.Group):
    def __init__(self, name: str, description: str, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    @discord.app_commands.command(description="Unloads all Slash Commands for Fred")
    async def unload_commands(self, interaction: discord.Interaction):
        for extension in other_extensions:
            try:
                await self.fred.unload_extension(extension)
            except discord.ext.commands.errors.ExtensionNotLoaded:
                logging.log(logging.INFO, f"Extension {extension} not loaded.")
        await self.fred.tree.sync()
        await interaction.response.send_message("All commands unloaded", ephemeral=True)

    @discord.app_commands.command(description="Loads all Slash Commands for Fred")
    async def load_commands(self, interaction: discord.Interaction):
        for extension in other_extensions:
            try:
                await self.fred.load_extension(extension)
            except discord.ext.commands.errors.ExtensionNotFound:
                logging.log(logging.INFO, f"Extension {extension} not found.")
                # await interaction.response.send_message("Error Loading Commands", ephemeral=True)
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                logging.log(logging.INFO, f"Extension {extension} already loaded.")
                # await interaction.response.send_message("Error Loading Commands", ephemeral=True)
        await self.fred.tree.sync()
        await interaction.response.send_message("All commands loaded", ephemeral=True)


async def setup(fred: Fred):
    fred.tree.add_command(FormstackCommands(name="admin", description="test", fred=fred))
