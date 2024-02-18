from __future__ import annotations

import datetime
import discord
import settings
from discord.ext import commands, tasks
import fred.w2w as w2w

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Branch
    from typing import Tuple, Dict

def vbs(branch: Branch, dt: datetime.datetime) -> Tuple[Dict[int, int], Dict[int, int]]:
    database = branch.ymca.database

    vats_by_sup = {}
    for discord_user in branch.guild.members:
        if branch.guild.get_role(branch.guild_role_ids['supervisor']) in discord_user.roles:
            # number of vats, number of shifts, ratio of vats per shift
            vats_by_sup[discord_user.id] = [0, 0, 'N/A']

    # Adding the number of VATs to each sup total
    vats = database.select_vats_mtd(branch, dt)
    for vat in vats:
        if vat.sup_discord_id in vats_by_sup:
            vats_by_sup[vat.sup_discord_id][0] += 1
            vats_by_sup[vat.sup_discord_id][1] = float(vats_by_sup[vat.sup_discord_id][0])


    vbs_incomplete = {}
    shift_dict_by_sup = branch.w2w_client.shifts_sorted_by_employee_id(datetime.date(dt.year, dt.month, 1), dt.date(), [branch.w2w_client.supervisor])
    for w2w_employee_id, shift_list in shift_dict_by_sup.items():
        discord_user = database.select_discord_user(branch, branch.get_w2w_employee_by_id(w2w_employee_id))
        if discord_user and discord_user.id in vats_by_sup:
            num_of_shifts = len(shift_list)
            num_of_vats = vats_by_sup[discord_user.id][0]
            ratio = num_of_vats / num_of_shifts
            if ratio < 0.75:
                vats_by_sup.pop(discord_user.id)
                vbs_incomplete[discord_user.id] = [num_of_vats, num_of_shifts, ratio]
            else:
                vats_by_sup[discord_user.id][1] = num_of_shifts
                vats_by_sup[discord_user.id][2] = ratio



    vbs_complete = {k: v for k, v in sorted(vats_by_sup.items(), key=lambda item: item[1][2], reverse=True)}
    vbs_incomplete = {k: v for k, v in sorted(vbs_incomplete.items(), key=lambda item: item[1][1])}
    return vbs_complete, vbs_incomplete

def vat_sup_dashboard(branch: Branch, dt: datetime.datetime) -> str:
    vbs_complete, vbs_incomplete = vbs(branch, dt)
    vbs_complete_formatted = [f'<@{id}>\nVATs: **{values[0]}**\t Shifts: **{values[1]}**\t Ratio: **{values[2]}**\n' for id, values in vbs_complete.items()]
    vbs_incomplete_formatted = [f'<@{id}>\nVATs: **{values[0]}**\t Shifts: **{values[1]}**\t Ratio: **{values[2]}**\n' for id, values in vbs_incomplete.items()]
    return f"{''.join(vbs_complete_formatted)}**--------------------**\n{''.join(vbs_incomplete_formatted)}"

def vbg(branch: Branch, dt: datetime.datetime) -> Tuple[Dict[int, int], Dict[int, int]]:
    database = branch.ymca.database

    vats_by_guard = {}
    for discord_user in branch.guild.members:
        if branch.guild.get_role(branch.guild_role_ids['lifeguard']) in discord_user.roles:
            vats_by_guard[discord_user.id] = 0

    # Adding the number of VATs to each guards total
    vats = database.select_vats_mtd(branch, dt)
    for vat in vats:
        if vat.guard_discord_id in vats_by_guard:
            vats_by_guard[vat.guard_discord_id] += 1

    # Splitting the guards into who has and hasn't been VATed for the month
    vbg_complete = {}
    vbg_incomplete = {}
    for guard, vats in vats_by_guard.items():
        if vats > 0:
            vbg_complete[guard] = vats
        else:
            vbg_incomplete[guard] = vats

    # Sort guards with completed VATs in that month, most VATs first
    vbg_complete = {k: v for k, v in sorted(vbg_complete.items(), key=lambda item: item[1], reverse=True)}

    return vbg_complete, vbg_incomplete
    

def vat_guard_dashboard(branch: Branch, dt: datetime.datetime) -> str:
    vbg_complete, vbg_incomplete = vbg(branch, dt)
    vats_complete_formatted = [f'<@{id}>: {num_of_vats}\n' for id, num_of_vats in vbg_complete.items()]
    vats_incomplete_formatted = [f'<@{id}>: {num_of_vats}\n' for id, num_of_vats in vbg_incomplete.items()]
    return f"{''.join(vats_complete_formatted)}**--------------------**\n{''.join(vats_incomplete_formatted)}"