from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Union, List
import fred.database_helper as dbh
import datetime

if TYPE_CHECKING:
    from .branch import Branch

def match_sample_location_key(keys: List[str]):
        for key in keys:
            if 'Location of Water Sample' in key:
                return key
        return None

@dataclass
class ChemCheck(object):
    chem_uuid: int
    chlorine: float
    ph: float
    discord_id: int = 0
    name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    sample_location: str = ''
    sample_time: Union[datetime.datetime, None] = None
    submit_time: Union[datetime.datetime, None] = None
    water_temp: str = ''
    num_of_swimmers: Union[int, None] = None
    
    @classmethod
    def from_csv_row(cls, branch: Branch, row: Dict[str, str]):
        chem_uuid = int(row['Unique ID'])
        discord_id = dbh.match_discord_id(branch, row['Your Name (First)'], row['Your Name (Last)'])
        name = dbh.handle_quotes(row['Your Name (First)'], row['Your Name (Last)'])
        pool_id = dbh.match_pool_id(branch, row.get('Western', ''))                
        sample_location = row.get('Location of Water Sample, Western', 'NULL')
        sample_time = dbh.handle_rss_datetime(row['Date/Time'])
        submit_time = dbh.handle_formstack_datetime(row['Time'])
        chlorine = float(row['Chlorine'])
        ph = float(row['PH'])
        water_temp = row['Water Temperature']
        num_of_swimmers = row['Total Number of Swimmers']
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, sample_time, submit_time,
                   water_temp, num_of_swimmers)
    
    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]):
        chem_uuid = int(entry['Unique ID'])
        discord_id = dbh.match_discord_id(branch, entry['Your Name'])
        name = dbh.handle_quotes(entry['Your Name'])
        pool_name_key = dbh.match_branch_name_alias(branch, entry.keys())
        pool_name = entry.get(pool_name_key, '')
        pool_id = dbh.match_pool_id(branch, pool_name)
        sample_location_key = match_sample_location_key(entry.keys())
        sample_location = entry.get(sample_location_key, '')
        sample_time = dbh.handle_rss_datetime(entry['Date/Time'])
        submit_time = entry['Time']
        chlorine = float(entry['Chlorine'])
        ph = float(entry['PH'])
        water_temp = entry['Water Temperature']
        num_of_swimmers = entry['Total Number of Swimmers'].strip()
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, sample_time, submit_time,
                   water_temp, num_of_swimmers)
    
