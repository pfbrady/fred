from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Union, List, Tuple
import fred.database_helper as dbh
import datetime

if TYPE_CHECKING:
    from .branch import Branch

def match_sample_location_key(keys: List[str]):
        for key in keys:
            if 'Location of Water Sample' in key:
                return key
        return None

def handle_water_temp(wt_str: str) -> float:
    return wt_str[:2] if 'degrees' in wt_str else 83

@dataclass
class ChemCheck(object):
    chem_uuid: int
    chlorine: float
    ph: float
    discord_id: Union[int, None] = None
    name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    sample_location: str = ''
    sample_time: Union[datetime.datetime, None] = None
    submit_time: Union[datetime.datetime, None] = None
    water_temp: str = ''
    num_of_swimmers: int = 0

    @property
    def cl_in_range(self) -> bool:
        return 0.1 < self.chlorine < 0.5
    
    @property
    def ph_in_range(self) -> bool:
        return 7.0 < self.ph < 8.0
    
    @classmethod
    def from_csv_row(cls, branch: Branch, row: Dict[str, str]):
        chem_uuid = int(row['Unique ID'])
        discord_id = dbh.match_discord_id(branch, row['Your Name (First)'], row['Your Name (Last)'])
        name = dbh.handle_quotes(row['Your Name (First)'], row['Your Name (Last)'])
        pool_id = dbh.match_pool_id_from_dict(branch, row)              
        sample_location = row.get('Location of Water Sample, Western', 'NULL')
        sample_time = dbh.handle_fs_rss_datetime(row['Date/Time'])
        submit_time = dbh.handle_fs_csv_datetime(row['Time'])
        chlorine = float(row['Chlorine'])
        ph = float(row['PH'])
        water_temp = handle_water_temp(row['Water Temperature'])
        num_of_swimmers = int(row['Total Number of Swimmers'])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, sample_time, submit_time,
                   water_temp, num_of_swimmers)
    
    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]):
        chem_uuid = int(entry['Unique ID'])
        discord_id = dbh.match_discord_id(branch, entry['Your Name'])
        name = dbh.handle_quotes(entry['Your Name'])
        pool_id = dbh.match_pool_id_from_dict(branch, entry)
        sample_location_key = match_sample_location_key(entry.keys())
        sample_location = entry.get(sample_location_key, '')
        sample_time = dbh.handle_fs_rss_datetime(entry['Date/Time'])
        submit_time = entry['Time']
        chlorine = float(entry['Chlorine'])
        ph = float(entry['PH'])
        water_temp = handle_water_temp(entry['Water Temperature'])
        num_of_swimmers = int(entry['Total Number of Swimmers'])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, sample_time, submit_time,
                   water_temp, num_of_swimmers)
    
    @classmethod
    def from_database(cls, db_tup: Tuple[str]):
        if not any(db_tup):
            return cls(0, 0.0, 0.0)
        chem_uuid = int(db_tup[0])
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        pool_id = db_tup[4]
        sample_location = db_tup[5]
        sample_time = datetime.datetime.fromisoformat(db_tup[6])
        submit_time = datetime.datetime.fromisoformat(db_tup[7])
        chlorine = float(db_tup[8])
        ph = float(db_tup[9])
        water_temp = int(db_tup[10])
        num_of_swimmers = int(db_tup[11])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch_id,
                   pool_id, sample_location, sample_time, submit_time,
                   water_temp, num_of_swimmers)
    
    def __bool__(self):
        return False if self.chem_uuid == 0 or None else True
