"""command_helper module"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from typing import List


async def platform_auto(interaction: discord.Interaction, current: str
                        ) -> List[discord.app_commands.Choice[str]]:
    """
    Autocomplete for any non-platform-agnostic slash command. To be used with
    commands that contain elements that output differently on mobile, such as
    @mentions and Embeds.
    
    Added with @discord.app_commands.autocomplete() decorator.

    Args:
        interaction (discord.Interaction): The interaction of a mobile-friendly
        slash command.
        current (str): The current string the user has typed so far.

    Returns:
        List[discord.app_commands.Choice[str]]: A list of arguments that a user
        can autocomplete the parameter with. 
    """
    return [
        discord.app_commands.Choice(name=default_pos, value=default_pos)
        for default_pos in ['mobile', 'desktop'] if current in default_pos
    ]
