from __future__ import annotations

from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from typing import List

async def mobile_auto(interaction: discord.Interaction, current: str
)-> List[discord.app_commands.Choice[str]]:
    return [
        discord.app_commands.Choice(name=default_pos, value=default_pos) 
        for default_pos in ['True', 'False'] if current in default_pos
    ]