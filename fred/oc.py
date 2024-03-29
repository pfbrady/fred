"""oc.py module"""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
import datetime
import fred.database_helper as dbh

if TYPE_CHECKING:
    from typing import Dict, Optional, Tuple
    from .branch import Branch


def get_regulatory_key_from_rss_keys(keys: list) -> str:
    """
    A helper function that gets the key corresponding to the regulatory
    information for a specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Opening/Closing Checklist RSS
        entry.

    Returns:
        str: The regulatory key
    """
    for key in keys:
        if 'Regulatory' in key:
            return key
    return ''

def get_cl_key_from_rss_keys(keys: list) -> str:
    """
    A helper function that gets the key corresponding to the chlorine reading
    for a specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Opening/Closing Checklist RSS
        entry.

    Returns:
        str: The chlorine key.
    """
    for key in keys:
        if 'CL reading' in key:
            return key
    return ''

def get_ph_key_from_rss_keys(keys: list) -> str:
    """
    A helper function that gets the key corresponding to the ph reading for a
    specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Opening/Closing Checklist RSS
        entry.

    Returns:
        str: The ph key.
    """
    for key in keys:
        if 'PH reading' in key:
            return key
    return ''

def get_water_temp_from_rss_keys(keys: list) -> str:
    """
    A helper function that gets the key corresponding to the water temperature
    reading for a specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Opening/Closing Checklist RSS
        entry.

    Returns:
        str: The water temperature key.
    """
    for key in keys:
        if 'water temperature' in key:
            return key
    return ''

def handle_water_temp(wt_str: str) -> int:
    """
    A helper function that gets the key corresponding to the chlorine reading
    for a specific pool at a specific branch.

    Args:
        keys (list): The keys of a Formstack Opening/Closing Checklist RSS
        entry.

    Returns:
        str: The chlorine key
    """
    return int(wt_str.split(' ')[0]) if '8' in wt_str else 83

def handle_cl(cl_str: str) -> float:
    """
    A helper function that extracts the clhorine reading from the formatted
    Formstack string.

    Args:
        cl_string (str): Answer to the 'What is the _________ CL reading' 
        question on the Formstack Opening/Closing Checklist Form.

    Returns:
        float: The chlorine ppm of the water.
    """
    if 'Around' in cl_str:
        return float(cl_str.split(' ')[1])
    elif cl_str == '0.5 or below':
        return 0.5
    elif cl_str == '5.0 or above':
        return 7.5

def handle_ph(ph_str: str) -> int:
    """
    A helper function that extracts the ph reading from the formatted
    Formstack string.

    Args:
        ph_string (str): Answer to the 'What is the _________ pH reading' 
        question on the Formstack Opening/Closing Checklist Form.

    Returns:
        float: The ph of the water.
    """
    if 'Around' in ph_str:
        return float(ph_str.split(' ')[1])
    elif ph_str == '7.0 or below':
        return 7.0
    elif ph_str == '8.0 of above':
        return 8.0
    else:
        return 7.5

def handle_vacuum_closing(entry: Dict[str, str]) -> bool:
    """
    A helper function that determines if the vacuum is operating properly.

    Args:
        entry (Dict[str, str]): A single entry from the RSS Feed.

    Returns:
        bool: if the vacuum is operating properly.
    """
    if entry.get('Does your supervisor expect you to place a robotic vacuum'
                 'into the pool?', '') == 'Yes':
        if entry.get(
            'Have you placed the robotic vacuum in the pool?', '') == 'Yes':
            if entry.get('Before leaving the Y, do you see the vacuum moving'
                         'across the pool bottom as expected?', '') == 'Yes':
                return True
    else:
        return False

@dataclass
class OpeningChecklist():
    """A representation of a Formstack Opening Checklist Submission."""
    oc_uuid: int
    discord_id: Optional[int] = None
    name: str = ''
    branch_id: str = ''
    checklist_group: str = ''
    time: Optional[datetime.datetime] = None
    submit_time: Optional[datetime.datetime] = None
    regulatory_info: str = ''
    aed_info: str = ''
    adult_pads_expiration_date: Optional[datetime.date] = None
    pediatric_pads_expiration_date: Optional[datetime.date] = None
    aspirin_expiration_date: Optional[datetime.date] = None
    sup_oxygen_info: str = ''
    sup_oxygen_psi: int = 0
    first_aid_info: str = ''
    chlorine: float = 0.0
    ph: float = 0.0
    water_temp: int = 0
    lights_function: bool = False
    handicap_chair_function: bool = False
    spare_battery_present: bool = False
    vacuum_present: bool = False

    @property
    def adult_pads_expired(self) -> bool:
        """
        Calculates if the expiration date for the adult pads is greater than the
        current date, based on the formstack response.

        Returns:
            bool: If the adult pads are expired.
        """
        return datetime.date.today() > self.adult_pads_expiration_date

    @property
    def pediatric_pads_expired(self) -> bool:
        """
        Calculates if the expiration date for the ped pads is greater than the
        current date, based on the formstack response.

        Returns:
            bool: If the ped pads are expired.
        """
        return datetime.date.today() > self.pediatric_pads_expiration_date

    @property
    def aspirin_expired(self) -> bool:
        """
        Calculates if the expiration date for the aspirin is greater than the
        current date, based on the formstack response.

        Returns:
            bool: If the aspirin is expired.
        """
        return datetime.date.today() > self.aspirin_expiration_date

    @classmethod
    def from_rss_entry(
            cls,
            branch: Branch,
            entry: Dict[str, str]
        ) -> OpeningChecklist:
        """
        Factory method that initializes an instance of OpeningChecklist from the
        Formstack RSS Feed.

        Args:
            branch (Branch): The YMCA Branch the RSS Feed is filtered for.
            entry (Dict[str, str]): A single entry from the RSS Feed.

        Returns:
            OpeningChecklist: An instance of OpeningChecklist
        """
        keys = entry.keys()
        oc_uuid = entry['Unique ID']
        discord_id = dbh.match_discord_id(
            branch, entry['Name of the individual completing the inspection'])
        name = dbh.handle_quotes(
            entry['Name of the individual completing the inspection'])
        checklist_group = entry.get('Which pool do you need to inspect?')
        time = dbh.handle_fs_rss_datetime_full_month(
            entry['Date & Time of Inspection'])
        submit_time = entry['Time']
        # Below values optional, thus use of .get()
        regulatory_info = dbh.handle_quotes(
            entry.get(get_regulatory_key_from_rss_keys(keys), ''))
        aed_info = entry.get('AED Inspection', '')
        adult_pads_expiration_date = dbh.handle_fs_rss_date(
            entry.get('What is the expiration date for the Adult Electrode Pads?'))
        pediatric_pads_expiration_date = dbh.handle_fs_rss_date(
            entry.get('What is the expiration date for the Pediatric Electrode Pads?'))
        aspirin_expiration_date = dbh.handle_fs_rss_date(
            entry.get('What is the expiration date of the Aspirin?'))
        sup_oxygen_info = entry.get('Supplemental Oxygen Inspection')
        sup_oxygen_psi = int(
            entry.get('What is the current pressure level of the oxygen tank?', 'Apx 0').split(" ")[1])
        first_aid_info = entry.get('First Aid Kit Inspection', '')
        chlorine = handle_cl(entry.get(get_cl_key_from_rss_keys(keys), ''))
        ph = handle_ph(entry.get(get_ph_key_from_rss_keys(keys), ''))
        water_temp = handle_water_temp(
            entry.get(get_water_temp_from_rss_keys(keys), ''))
        lights_function = False
        handicap_chair_function = entry.get(
            'Does the handicap chair function as required for usage by guests?') == 'Yes'
        spare_battery_present = entry.get(
            'Is there a spare battery available for the handicap chair?') == 'Yes'
        vacuum_present = entry.get(
            'Did you have to remove the robotic vacuum from the pool before opening?') == 'Yes'
        return cls(oc_uuid, discord_id, name, branch.branch_id,
                   checklist_group, time, submit_time, regulatory_info,
                   aed_info, adult_pads_expiration_date,
                   pediatric_pads_expiration_date, aspirin_expiration_date,
                   sup_oxygen_info, sup_oxygen_psi, first_aid_info, chlorine,
                   ph, water_temp, lights_function, handicap_chair_function,
                   spare_battery_present, vacuum_present)

    @classmethod
    def from_database(cls, db_tup: Tuple[str]) -> OpeningChecklist:
        """
        Factory method that initializes an instance of OpeningChecklist from a
        connected SQLite Database.

        Args:
            db_tup (Tuple[str]): Tuple returned by the sqlite3 'fetch'
            collection of methods.

        Returns:
            OpeningChecklist: An instance of OpeningChecklist
        """
        if not any(db_tup):
            return cls(0)
        oc_uuid = db_tup[0]
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        checklist_group = db_tup[4]
        time = datetime.datetime.fromisoformat(
            db_tup[5]) if db_tup[5] else None
        submit_time = datetime.datetime.fromisoformat(
            db_tup[6]) if db_tup[6] else None
        # Below values optional, thus use of .get()
        regulatory_info = db_tup[7]
        aed_info = db_tup[8]
        adult_pads_expiration_date = datetime.date.fromisoformat(
            db_tup[9]) if db_tup[9] else None
        pediatric_pads_expiration_date = datetime.date.fromisoformat(
            db_tup[10]) if db_tup[10] else None
        aspirin_expiration_date = datetime.date.fromisoformat(
            db_tup[11]) if db_tup[11] else None
        sup_oxygen_info = db_tup[12]
        sup_oxygen_psi = int(db_tup[13])
        first_aid_info = db_tup[14]
        chlorine = float(db_tup[15])
        ph = float(db_tup[16])
        water_temp = int(db_tup[17])
        lights_function = bool(db_tup[18])
        handicap_chair_function = bool(db_tup[19])
        spare_battery_present = bool(db_tup[20])
        vacuum_present = bool(db_tup[21])
        return cls(oc_uuid, discord_id, name, branch_id,
                   checklist_group, time, submit_time, regulatory_info,
                   aed_info, adult_pads_expiration_date,
                   pediatric_pads_expiration_date, aspirin_expiration_date,
                   sup_oxygen_info, sup_oxygen_psi, first_aid_info, chlorine,
                   ph, water_temp, lights_function, handicap_chair_function,
                   spare_battery_present, vacuum_present)

    def __bool__(self):
        return self.oc_uuid != 0 or self.oc_uuid is not None

@dataclass
class ClosingChecklist():
    """A representation of a Formstack Closing Checklist Submission."""
    oc_uuid: int
    discord_id: Optional[int] = None
    name: str = ''
    branch_id: str = ''
    checklist_group: str = ''
    time: Optional[datetime.datetime] = None
    submit_time: Optional[datetime.datetime] = None
    regulatory_info: str = ''
    chlorine: float = 0.0
    ph: float = 0.0
    water_temp: int = 0
    lights_function: bool = False
    vacuum_function: bool = False

    @classmethod
    def from_rss_entry(
            cls,
            branch: Branch,
            entry: Dict[str, str]) -> OpeningChecklist:
        """
        Factory method that initializes an instance of ClosingChecklist from the
        Formstack RSS Feed.

        Args:
            branch (Branch): The YMCA Branch the RSS Feed is filtered for.
            entry (Dict[str, str]): A single entry from the RSS Feed.

        Returns:
            ClosingChecklist: An instance of ClosingChecklist
        """
        keys = entry.keys()
        oc_uuid = entry['Unique ID']
        discord_id = dbh.match_discord_id(
            branch, entry['Name of the individual completing the inspection'])
        name = dbh.handle_quotes(
            entry['Name of the individual completing the inspection'])
        checklist_group = entry['Which pool do you need to inspect?']
        time = dbh.handle_fs_rss_datetime_full_month(
            entry['Date & Time of Inspection'])
        submit_time = entry['Time']
        # Below values optional, thus use of .get()
        regulatory_info = dbh.handle_quotes(
            entry.get(get_regulatory_key_from_rss_keys(keys), ''))
        chlorine = handle_cl(entry.get(get_cl_key_from_rss_keys(keys), ''))
        ph = handle_ph(entry.get(get_ph_key_from_rss_keys(keys), ''))
        water_temp = handle_water_temp(
            entry.get(get_water_temp_from_rss_keys(keys), ''))
        lights_function = False
        vacuum_function = handle_vacuum_closing(entry)
        return cls(oc_uuid, discord_id, name, branch.branch_id, checklist_group,
                   time, submit_time, regulatory_info, chlorine, ph, water_temp,
                   lights_function, vacuum_function)

    @classmethod
    def from_database(cls, db_tup: Tuple[str]) -> OpeningChecklist:
        """
        Factory method that initializes an instance of ClosingChecklist from a
        connected SQLite Database.

        Args:
            db_tup (Tuple[str]): Tuple returned by the sqlite3 'fetch'
            collection of methods.

        Returns:
            ClosingChecklist: An instance of ClosingChecklist
        """
        if not any(db_tup):
            return cls(0)
        oc_uuid = db_tup[0]
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        checklist_group = db_tup[4]
        time = datetime.datetime.fromisoformat(db_tup[5])
        submit_time = datetime.datetime.fromisoformat(db_tup[6])
        regulatory_info = db_tup[7]
        chlorine = float(db_tup[8])
        ph = float(db_tup[9])
        water_temp = int(db_tup[10])
        lights_function = bool(db_tup[11])
        vacuum_function = bool(db_tup[12])
        return cls(oc_uuid, discord_id, name, branch_id, checklist_group, time,
                   submit_time, regulatory_info, chlorine, ph, water_temp,
                   lights_function, vacuum_function)

    def __bool__(self):
        return self.oc_uuid != 0 or self.oc_uuid is not None
        