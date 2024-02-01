from __future__ import annotations

from typing import TYPE_CHECKING, Union, List
import datetime
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from .branch import Branch

def match_discord_id(branch: Branch, name: str, last_name: str = None) -> Union[int, str]:
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
            potential_match = (discord_user.id, first_name_match)
    return potential_match[0] if potential_match[0] else 'NULL'

def match_pool_id(branch: Branch, pool_alias: str) -> str:
    for pool_group in branch.pool_groups:
        for pool in pool_group.pools:
            if pool_alias in pool.aliases:
                return pool.pool_id
    return 'NULL'

def match_branch_name_alias(branch: Branch, keys: List[str]):
    for key in keys:
        if key == branch.name:
            return key
        if key in branch.aliases:
            return key
    return ''

def handle_quotes(*names: str):
    return ' '.join([name.strip().replace("'", "''") for name in names])

def handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(self, formstack_time: str):
    return datetime.datetime.strptime(formstack_time, '%B %d, %Y %I:%M %p')

def handle_rss_datetime(self, formstack_time: str):
    return datetime.datetime.strptime(formstack_time, '%b %d, %Y %I:%M %p')

def handle_rss_date(self, formstack_time: str):
    return datetime.datetime.strptime(formstack_time, '%b %d, %Y')

def handle_formstack_datetime(self, formstack_time: str):
    return datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S')