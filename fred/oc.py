from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Dict, Union, Tuple
import fred.database_helper as dbh
import datetime

if TYPE_CHECKING:
    from .branch import Branch

def get_regulatory_key_from_rss_keys(keys: list):
        for key in keys:
            if 'Regulatory' in key:
                return key
        return ''

def get_cl_key_from_rss_keys(keys: list):
        for key in keys:
            if 'CL reading' in key:
                return key
        return ''

def get_ph_key_from_rss_keys(keys: list):
        for key in keys:
            if 'PH reading' in key:
                return key
        return ''

def get_water_temp_from_rss_keys(keys: list):
        for key in keys:
            if 'water temperature' in key:
                return key
        return ''

def handle_water_temp(wt_str: str) -> int:
    return int(wt_str.split(' ')[0]) if '8' in wt_str else 83

def handle_cl(cl_str: str) -> float:
     if 'Around' in cl_str:
        return float(cl_str.split(' ')[1])
     elif cl_str == '0.5 or below':
        return 0.5
     elif cl_str == '5.0 or above':
        return 7.5
     
def handle_ph(ph_str: str) -> int:
    if 'Around' in ph_str:
        return float(ph_str.split(' ')[1])
    elif ph_str == '7.0 or below':
        return 7.0
    elif ph_str == '8.0 of above':
        return 8.0
    else:
        return 7.5

def handle_vacuum_closing(entry: dict) -> bool:
    if entry.get('Does your supervisor expect you to place a robotic vacuum into the pool?', '') == 'Yes':
        if entry.get('Have you placed the robotic vacuum in the pool?', '') == 'Yes':
            if entry.get('Before leaving the Y, do you see the vacuum moving across the pool bottom as expected?', '') == 'Yes':
                return True
    else:
        return False

@dataclass
class OpeningChecklist(object):
    oc_uuid: int
    discord_id: Union[int, None] = None
    name: str = ''
    branch_id: str = ''
    checklist_group: str = ''
    opening_time: Union[datetime.datetime, None] = None
    submit_time: Union[datetime.datetime, None] = None
    regulatory_info: str = ''
    aed_info: str = ''
    adult_pads_expiration_date: Union[datetime.date, None] = None
    pediatric_pads_expiration_date: Union[datetime.date, None] = None
    aspirin_expiration_date: Union[datetime.date, None] = None
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
        return datetime.date.today() > self.adult_pads_expiration_date
    
    @property
    def pediatric_pads_expired(self) -> bool:
        return datetime.date.today() > self.pediatric_pads_expiration_date
    
    @property
    def aspirin_expired(self) -> bool:
        return datetime.date.today() > self.aspirin_expiration_date
    
    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]):
        keys = entry.keys()
        oc_uuid = entry['Unique ID']
        discord_id = dbh.match_discord_id(branch, entry['Name of the individual completing the inspection'])
        name = dbh.handle_quotes(entry['Name of the individual completing the inspection'])
        checklist_group = entry.get('Which pool do you need to inspect?')
        opening_time = dbh.handle_fs_rss_datetime_full_month(entry['Date & Time of Inspection'])
        submit_time = entry['Time']
        # Below values optional, thus use of .get()
        regulatory_info = dbh.handle_quotes(entry.get(get_regulatory_key_from_rss_keys(keys), ''))
        aed_info = entry.get('AED Inspection', '')
        adult_pads_expiration_date = dbh.handle_fs_rss_date(entry.get('What is the expiration date for the Adult Electrode Pads?'))
        pediatric_pads_expiration_date = dbh.handle_fs_rss_date(entry.get('What is the expiration date for the Pediatric Electrode Pads?'))
        aspirin_expiration_date = dbh.handle_fs_rss_date(entry.get('What is the expiration date of the Aspirin?'))
        sup_oxygen_info = entry.get('Supplemental Oxygen Inspection')
        sup_oxygen_psi = int(entry.get('What is the current pressure level of the oxygen tank?', 'Apx 0').split(" ")[1])
        first_aid_info = entry.get('First Aid Kit Inspection', '')
        chlorine = handle_cl(entry.get(get_cl_key_from_rss_keys(keys), ''))
        ph = handle_ph(entry.get(get_ph_key_from_rss_keys(keys), ''))
        water_temp = handle_water_temp(entry.get(get_water_temp_from_rss_keys(keys), ''))
        lights_function = False
        handicap_chair_function = True if entry.get('Does the handicap chair function as required for usage by guests?') == 'Yes' else False
        spare_battery_present = True if entry.get('Is there a spare battery available for the handicap chair?') == 'Yes' else False
        vacuum_present = True if entry.get('Did you have to remove the robotic vacuum from the pool before opening?') == 'Yes' else False
        return cls(oc_uuid, discord_id, name, branch.branch_id, checklist_group, opening_time, submit_time, 
                   regulatory_info, aed_info, adult_pads_expiration_date, pediatric_pads_expiration_date,
                   aspirin_expiration_date, sup_oxygen_info, sup_oxygen_psi, first_aid_info, chlorine, ph, water_temp,
                   lights_function, handicap_chair_function, spare_battery_present, vacuum_present)
    
    @classmethod
    def from_database(cls, db_tup: Tuple[str]):
        oc_uuid = db_tup[0]
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        checklist_group = db_tup[4]
        opening_time = datetime.datetime.fromisoformat(db_tup[5]) if db_tup[5] else None
        submit_time = datetime.datetime.fromisoformat(db_tup[6]) if db_tup[6] else None
        # Below values optional, thus use of .get()
        regulatory_info = db_tup[7]
        aed_info = db_tup[8]
        adult_pads_expiration_date = datetime.date.fromisoformat(db_tup[9]) if db_tup[9] else None
        pediatric_pads_expiration_date = datetime.date.fromisoformat(db_tup[10]) if db_tup[10] else None
        aspirin_expiration_date = datetime.date.fromisoformat(db_tup[11]) if db_tup[11] else None
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
        return cls(oc_uuid, discord_id, name, branch_id, checklist_group, opening_time, submit_time, 
                   regulatory_info, aed_info, adult_pads_expiration_date, pediatric_pads_expiration_date,
                   aspirin_expiration_date, sup_oxygen_info, sup_oxygen_psi, first_aid_info, chlorine, ph, water_temp,
                   lights_function, handicap_chair_function, spare_battery_present, vacuum_present)

@dataclass
class ClosingChecklist(object):
    oc_uuid: int
    discord_id: Union[int, None] = None
    name: str = ''
    branch_id: str = ''
    checklist_group: str = ''
    closing_time: Union[datetime.datetime, None] = None
    submit_time: Union[datetime.datetime, None] = None
    regulatory_info: str = ''
    chlorine: float = 0.0
    ph: float = 0.0
    water_temp: int = 0
    lights_function: bool = False
    vacuum_function: bool = False

    @classmethod
    def from_rss_entry(cls, branch: Branch, entry: Dict[str, str]):
        keys = entry.keys()
        oc_uuid = entry['Unique ID']
        discord_id = dbh.match_discord_id(branch, entry['Name of the individual completing the inspection'])
        name = dbh.handle_quotes(entry['Name of the individual completing the inspection'])
        checklist_group = entry['Which pool do you need to inspect?']
        closing_time = dbh.handle_fs_rss_datetime_full_month(entry['Date & Time of Inspection'])
        submit_time = entry['Time']
        # Below values optional, thus use of .get()
        regulatory_info = dbh.handle_quotes(entry.get(get_regulatory_key_from_rss_keys(keys), ''))
        chlorine = handle_cl(entry.get(get_cl_key_from_rss_keys(keys), ''))
        ph = handle_ph(entry.get(get_ph_key_from_rss_keys(keys), ''))
        water_temp = handle_water_temp(entry.get(get_water_temp_from_rss_keys(keys), ''))
        lights_function = False
        vacuum_function = handle_vacuum_closing(entry)
        return cls(oc_uuid, discord_id, name, branch.branch_id, checklist_group, closing_time, submit_time, 
                   regulatory_info, chlorine, ph, water_temp, lights_function, vacuum_function)
    
    @classmethod
    def from_database(cls, db_tup: Tuple[str]):
        oc_uuid = db_tup[0]
        discord_id = int(db_tup[1]) if db_tup[1] else None
        name = db_tup[2]
        branch_id = db_tup[3]
        checklist_group = db_tup[4]
        closing_time = datetime.datetime.fromisoformat(db_tup[5])
        submit_time = datetime.datetime.fromisoformat(db_tup[6])
        # Below values optional, thus use of .get()
        regulatory_info = db_tup[7]
        chlorine = float(db_tup[8])
        ph = float(db_tup[9])
        water_temp = int(db_tup[10])
        lights_function = bool(db_tup[11])
        vacuum_function = bool(db_tup[12])
        return cls(oc_uuid, discord_id, name, branch_id, checklist_group, closing_time, submit_time, 
                   regulatory_info, chlorine, ph, water_temp, lights_function, vacuum_function)