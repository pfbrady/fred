from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Dict, Union, Tuple
import fred.database_helper as dbh
import datetime

if TYPE_CHECKING:
    from .branch import Branch

    
def handle_depth(depth_string: str) -> float:
    if depth_string == 'Less than 1 Foot of Water':
        return 0.5
    if depth_string == '12 Feet or Greater':
        return 12.0
    else:
        depth_list = depth_string.split(' ')
        depth_list = depth_list[0].split('-')
        return (float(depth_list[0]) + float(depth_list[1])) / 2
    
def handle_response_time(pass_string: str):
    if pass_string == 'Yes (10 seconds or less)':
        return 10.0
    elif 'seconds' in pass_string:
        pass_list = pass_string.split(' ')
        return (float(pass_list[1][1:]) + float(pass_list[3])) / 2
    else:
        return 60.0

@dataclass
class VAT(object):
    vat_uuid: int
    guard_discord_id: Union[int, None] = None
    guard_name: str = ''
    sup_discord_id: Union[int, None] = None
    sup_name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    vat_time: Union[datetime.datetime, None] = None
    submit_time: Union[datetime.datetime, None] = None
    num_of_swimmers: int = 0
    num_of_guards: int = 0
    stimuli: str = ''
    depth: float = 0.0
    response_time: float = 0.0

    @property
    def vat_pass(self) -> bool:
        return True if self.response_time > 10.0 else False
    
    @classmethod
    def from_csv_row(cls, branch: Branch, row: Dict[str, str]):
        vat_uuid = int(row['Unique ID'])
        guard_discord_id = dbh.match_discord_id(
            branch,
            row['Name of Lifeguard Vigilance Tested (First)'],
            row['Name of Lifeguard Vigilance Tested (Last)'])
        guard_name = dbh.handle_quotes(
            row['Name of Lifeguard Vigilance Tested (First)'],
            row['Name of Lifeguard Vigilance Tested (Last)'])
        sup_discord_id = dbh.match_discord_id(
            branch,
            row['Who monitored & conducted the vigilance test? (First)'],
            row['Who monitored & conducted the vigilance test? (Last)'])
        sup_name = dbh.handle_quotes(
            row['Who monitored & conducted the vigilance test? (First)'],
            row['Who monitored & conducted the vigilance test? (Last)'])
        if row['Which Pool? - Western']:
            pool_id = dbh.match_pool_id(branch, row['Which Pool? - Western'])
        else:
            pool_id = dbh.match_pool_id(branch, row['Which Pool? '])
        if row['Date & Time of Vigilance Test Conducted']:
            vat_time = dbh.handle_fs_rss_datetime_full_month(row['Date & Time of Vigilance Test Conducted'])
        else:
            vat_time = dbh.handle_fs_rss_datetime(
                f"{row['Date of Vigilance Test Conducted']} {row['Time of Vigilance Test Conducted ']}")
        submit_time = dbh.handle_fs_csv_datetime(row['Time'])
        num_of_swimmers = dbh.handle_num_of_guests(row['How many guests do you believe were in the pool?'])
        num_of_guards = dbh.handle_num_of_guards(row['Were they the only lifeguard watching the pool?'])
        stimuli = row['What type of stimuli was used?']
        depth = handle_depth(row['What was the water depth where the stimuli was placed?'])
        response_time = handle_response_time(row['Did the lifeguard being vigilance tested respond to the stimuli?'])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id, sup_name, branch.branch_id, pool_id, 
                   vat_time, submit_time, num_of_swimmers, num_of_guards, stimuli, depth, response_time)
    
    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]):
        vat_uuid = int(entry['Unique ID'])
        guard_discord_id = dbh.match_discord_id(branch, entry['Name of Lifeguard Vigilance Tested'])
        guard_name = dbh.handle_quotes(entry['Name of Lifeguard Vigilance Tested'])
        sup_discord_id = dbh.match_discord_id(branch, entry['Who monitored & conducted the vigilance test?'])
        sup_name = dbh.handle_quotes(entry['Who monitored & conducted the vigilance test?'])
        pool_id = dbh.match_pool_id(branch, entry['Which Pool? '])
        vat_time = dbh.handle_fs_rss_datetime(
            f"{entry['Date of Vigilance Test Conducted']} {entry['Time of Vigilance Test Conducted ']}")
        submit_time = entry['Time']
        num_of_swimmers = dbh.handle_num_of_guests(entry['How many guests do you believe were in the pool?'])
        num_of_guards = dbh.handle_num_of_guards(entry['Were they the only lifeguard watching the pool?'])
        stimuli = entry['What type of stimuli was used?']
        depth = handle_depth(entry['What was the water depth where the stimuli was placed?'])
        response_time = handle_response_time(entry['Did the lifeguard being vigilance tested respond to the stimuli?'])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id, sup_name, branch.branch_id, pool_id, 
                   vat_time, submit_time, num_of_swimmers, num_of_guards, stimuli, depth, response_time)
    
    @classmethod
    def from_database(cls, db_tup: Tuple[str]):
        if not any(db_tup):
            return cls(0)
        vat_uuid = int(db_tup[0])
        guard_discord_id = int(db_tup[1]) if db_tup[1] else None
        guard_name = db_tup[2]
        sup_discord_id = int(db_tup[3]) if db_tup[3] else None
        sup_name = db_tup[4]
        branch_id = db_tup[5]
        pool_id = db_tup[6]
        vat_time = datetime.datetime.fromisoformat(db_tup[7])
        submit_time = datetime.datetime.fromisoformat(db_tup[8])
        num_of_swimmers = int(db_tup[9])
        num_of_guards = int(db_tup[10])
        stimuli = db_tup[11]
        depth = float(db_tup[12])
        response_time = float(db_tup[13])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id, sup_name, branch_id, pool_id, 
                   vat_time, submit_time, num_of_swimmers, num_of_guards, stimuli, depth, response_time)
    
    def __bool__(self):
        return False if self.vat_uuid == 0 or None else True