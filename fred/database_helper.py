from __future__ import annotations

from typing import TYPE_CHECKING, Union, List, ItemsView
import datetime
import logging
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from .branch import Branch

def match_discord_id(branch: Branch, name: str, last_name: str = None) -> Union[int, None]:
    if not last_name:
        split_name = name.split(' ', 1)
        if len(split_name) == 1:
            name, last_name = (split_name[0], '')
        else:
            name, last_name = split_name
    potential_match = (0, 0)
    for discord_user in branch.guild.members:
        discord_display_name_split = discord_user.display_name.lower().split(' ', 1)
        last_name_match = SequenceMatcher(None, discord_display_name_split[-1], last_name.lower()).ratio()
        first_name_match = SequenceMatcher(None, discord_display_name_split[0], name.lower()).ratio()
        if last_name_match > 0.85 and first_name_match > potential_match[1]:
            potential_match = discord_user.id, first_name_match
    return potential_match[0] if potential_match[0] else None

def match_pool_id(branch: Branch, pool_alias: str) -> str:
    for pool_group in branch.pool_groups:
        for pool in pool_group.pools:
            if pool_alias in pool.aliases:
                return pool.pool_id
    return ''

def match_pool_id_from_dict(branch: Branch, form: dict):
    for key, item in form.items():
        if key == branch.name:
            return match_pool_id(branch, item)
        if key in branch.aliases:
            return match_pool_id(branch, item)
    return ''

def handle_quotes(*names: str) -> str:
    return ' '.join([name.strip().replace("'", "''") for name in names])

def handle_fs_rss_date(date_string: str) -> Union[datetime.date, None]:
        d_formatted = None
        try:
            d_formatted = datetime.datetime.strptime(date_string, '%b %d, %Y').date()
        except Exception as e:
            logging.log(logging.WARN, f"RSS date ({date_string}) not formatted correcty: {e}")
        
        return d_formatted

def handle_fs_rss_datetime_full_month(time_str: str) -> Union[datetime.datetime, None]:
    dt_formatted = None
    try:
        dt_formatted = datetime.datetime.strptime(time_str, '%B %d, %Y %I:%M %p')
    except Exception as e:
        logging.log(logging.WARN, f"RSS datetime ({time_str}) not formatted correcty: {e}")
    
    return dt_formatted

def handle_fs_rss_datetime(time_str: str) -> Union[datetime.datetime, None]:
    dt_formatted = None
    try:
        dt_formatted = datetime.datetime.strptime(time_str, '%b %d, %Y %I:%M %p')
        return dt_formatted
    except Exception as e:
        logging.log(logging.WARN, f"RSS datetime ({time_str}) not formatted correcty: {e}")

    return dt_formatted

def handle_fs_csv_datetime(time_str: str) -> Union[datetime.datetime, None]:
    dt_formatted = None
    try:
        dt_formatted = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return dt_formatted
    except Exception as e:
        logging.log(logging.WARN, f"Formstack datetime ({time_str}) not formatted correcty: {e}")

    return dt_formatted

def handle_num_of_guests(guests_string: str):
    guests_list = guests_string.split(' ')
    try:
        return int(guests_list[-2])
    except ValueError as e:
        logging.warning(f"Error: Number of Guests field improperly filled out on Formstack {e}")
        return 10
        
def handle_num_of_guards(guards_string: str):
    if guards_string == 'Yes':
        return 1
    else:
        guards_list = guards_string.split(' ')
        return int(guards_list[3])