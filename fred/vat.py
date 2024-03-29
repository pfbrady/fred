"""VAT Module"""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
import datetime
import fred.database_helper as dbh

if TYPE_CHECKING:
    from typing import Dict, Optional, Tuple
    from .branch import Branch


def handle_depth(depth_string: str) -> float:
    """
    A helper function that extracts the depth of a VAT from the formatted
    Formstack string.

    Args:
        depth_string (str): Answer to the 'What was the water depth where the
        stimuli was placed?' questionnon the Formstack VAT Form.

    Returns:
        float: The depth of the VAT stimuli.
    """
    if depth_string == 'Less than 1 Foot of Water':
        return 0.5
    if depth_string == '12 Feet or Greater':
        return 12.0
    depth_list = depth_string.split(' ')
    depth_list = depth_list[0].split('-')
    return (float(depth_list[0]) + float(depth_list[1])) / 2

def handle_response_time(pass_string: str):
    """
    A helper function that extracts the response time to a VAT from the
    formatted Formstack string.

    Args:
        pass_string (str): Answer to the 'What was the water depth where the
        stimuli was placed?' question on the Formstack VAT Form.

    Returns:
        _type_: The amount of time the lifeguard took to notice the VAT.
    """
    if pass_string == 'Yes (10 seconds or less)':
        return 10.0
    if 'seconds' in pass_string:
        pass_list = pass_string.split(' ')
        return (float(pass_list[1][1:]) + float(pass_list[3])) / 2
    return 60.0

@dataclass
class VAT():
    """A representation of a Formstack VAT Submission."""
    vat_uuid: int
    guard_discord_id: Optional[int] = None
    guard_name: str = ''
    sup_discord_id: Optional[int] = None
    sup_name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    time: Optional[datetime.datetime] = None
    submit_time: Optional[datetime.datetime] = None
    num_of_swimmers: int = 0
    num_of_guards: int = 0
    stimuli: str = ''
    depth: float = 0.0
    response_time: float = 0.0

    @property
    def vat_pass(self) -> bool:
        """Based on the response time, if the lifeguard passed the VAT."""
        return self.response_time >= 10.0

    @classmethod
    def from_csv_row(cls, branch: Branch, row: Dict[str, str]) -> VAT:
        """
        Factory method that initializes an instance of VAT from a CSV export
        from Formstack.

        Args:
            branch (Branch): The YMCA Branch the CSV file is filtered for.
            row (Dict[str, str]): A single row from the CSV file.

        Returns:
            VAT: An instance of VAT
        """
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
            time = dbh.handle_fs_rss_datetime_full_month(
                row['Date & Time of Vigilance Test Conducted'])
        else:
            time = dbh.handle_fs_rss_datetime(
                f"{row['Date of Vigilance Test Conducted']}"
                f"{ row['Time of Vigilance Test Conducted ']}")
        submit_time = dbh.handle_fs_csv_datetime(row['Time'])
        num_of_swimmers = dbh.handle_num_of_guests(
            row['How many guests do you believe were in the pool?'])
        num_of_guards = dbh.handle_num_of_guards(
            row['Were they the only lifeguard watching the pool?'])
        stimuli = row['What type of stimuli was used?']
        depth = handle_depth(
            row['What was the water depth where the stimuli was placed?'])
        response_time = handle_response_time(
            row['Did the lifeguard being vigilance tested respond to the stimuli?'])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id,
                   sup_name, branch.branch_id, pool_id, time, submit_time,
                   num_of_swimmers, num_of_guards, stimuli, depth,
                   response_time)

    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]) -> VAT:
        """
        Factory method that initializes an instance of VAT from the
        Formstack RSS Feed.

        Args:
            branch (Branch): The YMCA Branch the RSS Feed is filtered for.
            entry (Dict[str, str]): A single entry from the RSS Feed.

        Returns:
            VAT: An instance of VAT
        """
        vat_uuid = int(entry['Unique ID'])
        guard_discord_id = dbh.match_discord_id(
            branch,
            entry['Name of Lifeguard Vigilance Tested'])
        guard_name = dbh.handle_quotes(
            entry['Name of Lifeguard Vigilance Tested'])
        sup_discord_id = dbh.match_discord_id(
            branch,
            entry['Who monitored & conducted the vigilance test?'])
        sup_name = dbh.handle_quotes(
            entry['Who monitored & conducted the vigilance test?'])
        pool_id = dbh.match_pool_id(branch, entry['Which Pool? '])
        time = dbh.handle_fs_rss_datetime(
            f"{entry['Date of Vigilance Test Conducted']}"
            f" {entry['Time of Vigilance Test Conducted ']}")
        submit_time = entry['Time']
        num_of_swimmers = dbh.handle_num_of_guests(
            entry['How many guests do you believe were in the pool?'])
        num_of_guards = dbh.handle_num_of_guards(
            entry['Were they the only lifeguard watching the pool?'])
        stimuli = entry['What type of stimuli was used?']
        depth = handle_depth(
            entry['What was the water depth where the stimuli was placed?'])
        response_time = handle_response_time(
            entry['Did the lifeguard being vigilance tested respond to the stimuli?'])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id,
                   sup_name, branch.branch_id, pool_id, time, submit_time,
                   num_of_swimmers, num_of_guards, stimuli, depth,
                   response_time)

    @classmethod
    def from_database(cls, db_tup: Tuple[str]) -> VAT:
        """
        Factory method that initializes an instance of VAT from a connected
        SQLite Database.

        Args:
            db_tup (Tuple[str]): Tuple returned by the sqlite3 'fetch'
            collection of methods.

        Returns:
            VAT: An instance of VAT
        """
        if not any(db_tup):
            return cls(0)
        vat_uuid = int(db_tup[0])
        guard_discord_id = int(db_tup[1]) if db_tup[1] else None
        guard_name = db_tup[2]
        sup_discord_id = int(db_tup[3]) if db_tup[3] else None
        sup_name = db_tup[4]
        branch_id = db_tup[5]
        pool_id = db_tup[6]
        time = datetime.datetime.fromisoformat(db_tup[7])
        submit_time = datetime.datetime.fromisoformat(db_tup[8])
        num_of_swimmers = int(db_tup[9])
        num_of_guards = int(db_tup[10])
        stimuli = db_tup[11]
        depth = float(db_tup[12])
        response_time = float(db_tup[13])
        return cls(vat_uuid, guard_discord_id, guard_name, sup_discord_id,
                   sup_name, branch_id, pool_id, time, submit_time,
                   num_of_swimmers, num_of_guards, stimuli, depth,
                   response_time)

    def __bool__(self):
        return self.vat_uuid != 0
