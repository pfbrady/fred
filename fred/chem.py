"""chem.py module"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
import datetime
import fred.database_helper as dbh

if TYPE_CHECKING:
    from typing import Dict, List, Tuple, Optional
    from .branch import Branch

def match_sample_location_key(keys: List[str]) -> str:
    """
    A helper function that gets the key corresponding to the sample location
    for a specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Chemical Check RSS entry.

    Returns:
        str: The sample location key.
    """
    for key in keys:
        if 'Location of Water Sample' in key:
            return key
    return ''

def handle_water_temp(wt_str: str) -> float:
    """
    A helper function that extracts the water temperature taken duing a Chemical
    Check from the Formstack string.

    Args:
        wt_str (str): Answer to the 'Water Temperature' question on the
        Formstack Chemical Check Form.

    Returns:
        float: The water temperature.
    """
    return wt_str[:2] if 'degrees' in wt_str else 83

@dataclass
class ChemCheck():
    """A representation of a Formstack Chemical Check Submission."""
    chem_uuid: int
    chlorine: float
    ph: float
    discord_id: Optional[int] = None
    name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    sample_location: str = ''
    time: Optional[datetime.datetime] = None
    submit_time: Optional[datetime.datetime] = None
    water_temp: str = ''
    num_of_swimmers: int = 0

    @property
    def cl_in_range(self) -> bool:
        """
        Based on the chlorine reading, determines if the chlorine is in proper
        range for the pool.
        """
        return 0.1 < self.chlorine < 0.5

    @property
    def ph_in_range(self) -> bool:
        """
        Based on the pH reading, determines if the pH is in proper range for
        the pool.
        """
        return 7.0 < self.ph < 8.0

    @classmethod
    def from_csv_row(cls, branch: Branch, row: Dict[str, str]) -> ChemCheck:
        """
        Factory method that initializes an instance of ChemCheck from a CSV 
        export from Formstack.

        Args:
            branch (Branch): The YMCA Branch the CSV file is filtered for.
            row (Dict[str, str]): A single row from the CSV file.

        Returns:
            ChemCheck: An instance of ChemCheck
        """
        chem_uuid = int(row['Unique ID'])
        discord_id = dbh.match_discord_id(branch, row['Your Name (First)'], row['Your Name (Last)'])
        name = dbh.handle_quotes(row['Your Name (First)'], row['Your Name (Last)'])
        pool_id = dbh.match_pool_id_from_dict(branch, row)
        sample_location = row.get('Location of Water Sample, Western', 'NULL')
        time = dbh.handle_fs_rss_datetime(row['Date/Time'])
        submit_time = dbh.handle_fs_csv_datetime(row['Time'])
        chlorine = float(row['Chlorine'])
        ph = float(row['PH'])
        water_temp = handle_water_temp(row['Water Temperature'])
        num_of_swimmers = int(row['Total Number of Swimmers'])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, time, submit_time,
                   water_temp, num_of_swimmers)

    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]) -> ChemCheck:
        """
        Factory method that initializes an instance of ChemCheck from the
        Formstack RSS Feed.

        Args:
            branch (Branch): The YMCA Branch the RSS Feed is filtered for.
            entry (Dict[str, str]): A single entry from the RSS Feed.

        Returns:
            VAT: An instance of VAT
        """
        chem_uuid = int(entry['Unique ID'])
        discord_id = dbh.match_discord_id(branch, entry['Your Name'])
        name = dbh.handle_quotes(entry['Your Name'])
        pool_id = dbh.match_pool_id_from_dict(branch, entry)
        sample_location_key = match_sample_location_key(entry.keys())
        sample_location = entry.get(sample_location_key, '')
        time = dbh.handle_fs_rss_datetime(entry['Date/Time'])
        submit_time = entry['Time']
        chlorine = float(entry['Chlorine'])
        ph = float(entry['PH'])
        water_temp = handle_water_temp(entry['Water Temperature'])
        num_of_swimmers = int(entry['Total Number of Swimmers'])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch.branch_id,
                   pool_id, sample_location, time, submit_time,
                   water_temp, num_of_swimmers)

    @classmethod
    def from_database(cls, db_tup: Tuple[str]) -> ChemCheck:
        """
        Factory method that initializes an instance of ChemCheck from a
        connected SQLite Database.

        Args:
            db_tup (Tuple[str]): Tuple returned by the sqlite3 'fetch'
            collection of methods.

        Returns:
            ChemCheck: An instance of ChemCheck
        """
        if not any(db_tup):
            return cls(0, 0.0, 0.0)
        chem_uuid = int(db_tup[0])
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        pool_id = db_tup[4]
        sample_location = db_tup[5]
        time = datetime.datetime.fromisoformat(db_tup[6])
        submit_time = datetime.datetime.fromisoformat(db_tup[7])
        chlorine = float(db_tup[8])
        ph = float(db_tup[9])
        water_temp = int(db_tup[10])
        num_of_swimmers = int(db_tup[11])
        return cls(chem_uuid, chlorine, ph, discord_id, name, branch_id,
                   pool_id, sample_location, time, submit_time,
                   water_temp, num_of_swimmers)

    def __bool__(self):
        return self.chem_uuid != 0
