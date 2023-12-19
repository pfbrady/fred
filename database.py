import sqlite3
import requests
import settings
import logging
import datetime
import csv
import datetime
import csv
import time
from typing import List
from discord.user import User as DicordUser
from difflib import SequenceMatcher
import rss

class YMCADatabase(object):

    connection: sqlite3.Connection = None

    def __init__(self):
        if YMCADatabase.connection is None:
            try:
                YMCADatabase.connection = sqlite3.connect("ymca_aquatics.db")
            except Exception as e:
                logging.warning(f"Error: Connection to database 'ymca_aquatics.db' not established {e}")
            else:
                logging.log(msg="Connection to database 'ymca_aquatics.db' established", level=logging.INFO)
                self.w2w_users = {key:[] for key in settings.SETTINGS_DICT['branches'].keys()}
                self.discord_users = {key:[] for key in settings.SETTINGS_DICT['branches'].keys()}
                self.init_tables()
                self.init_branches()
                self.form_tables = {'chem_checks': {'last_id': 0, 'rss': settings.CHEMS_RSS_007}, 
                      'vats': {'last_id': 0, 'rss': settings.VATS_RSS_007},
                      'opening_checklists': {'last_id': 0, 'rss': settings.OC_RSS_007},
                      'closing_checklists': {'last_id': 0, 'rss': settings.OC_RSS_007}
                    }
    def update_tables_rss(self):
        num_of_updates = {}
        for table, info in self.form_tables.items():
            table_num_of_updates = 0
            updated_rss = rss.form_rss_to_dict(info['rss'])
            if table == 'opening_checklists' or table == 'closing_checklists':
                updated_rss = [entry for entry in updated_rss if f"{entry['What checklist do you need to submit?'].replace(' ', '_').lower()}s" == table]
            for entry in updated_rss:
                if entry['Unique ID'] > info['last_id']:
                    table_num_of_updates += 1
                    self.insert_entry_rss(entry, table)
                    info['last_id'] = entry['Unique ID']
            num_of_updates[table] = table_num_of_updates
        return num_of_updates

    def insert_entry_rss(self, entry_dict: dict, table: str):
        cursor = self.connection.cursor()
        if table == 'chem_checks':
            discord_id = self.handle_names('007', entry_dict['Your Name'])
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO {table}
                    VALUES(
                        {entry_dict['Unique ID']},
                        {discord_id if discord_id else 'NULL'},
                        '{self.handle_quotes(entry_dict['Your Name'])}',
                        '{self.handle_branch(entry_dict['Branch'])}',
                        '{entry_dict['Western']}',
                        '{entry_dict['Location of Water Sample, Western']}',
                        '{self.handle_rss_datetime(entry_dict['Date/Time'])}',
                        '{entry_dict['Time']}',
                        {entry_dict['Chlorine']},
                        {entry_dict['PH']},
                        '{entry_dict['Water Temperature']}',
                        '{entry_dict['Total Number of Swimmers'].strip()}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"Chem Check (ID: {entry_dict['Unique ID']}) already in table 'chem_checks'")
            else:
                logging.log(msg=f"Chem Check (ID: {entry_dict['Unique ID']}) inserted into table 'chem_checks'", level=logging.INFO)
        elif table == 'vats':
            guard_discord_id = self.handle_names('007', entry_dict['Name of Lifeguard Vigilance Tested'])
            sup_discord_id = self.handle_names('007', entry_dict['Who monitored & conducted the vigilance test?'])
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO vats
                    VALUES(
                        {entry_dict['Unique ID']},
                        {guard_discord_id if guard_discord_id else 'NULL'},
                        '{self.handle_quotes(entry_dict['Name of Lifeguard Vigilance Tested'])}',
                        {sup_discord_id if sup_discord_id else 'NULL'},
                        '{self.handle_quotes(entry_dict['Who monitored & conducted the vigilance test?'])}',
                        '{self.handle_branch(entry_dict['YMCA of Delaware Branch'])}',
                        '{entry_dict['Which Pool? ']}',
                        '{self.handle_rss_datetime(f"{entry_dict['Date of Vigilance Test Conducted']} {entry_dict['Time of Vigilance Test Conducted ']}")}',
                        '{entry_dict['Time']}',
                        '{self.handle_num_of_guests(entry_dict['How many guests do you believe were in the pool?'])}',
                        '{self.handle_num_of_guards(entry_dict['Were they the only lifeguard watching the pool?'])}',
                        '{entry_dict['What type of stimuli was used?']}',
                        '{self.handle_depth(entry_dict['What was the water depth where the stimuli was placed?'])}',
                        '{self.handle_pass(entry_dict['Did the lifeguard being vigilance tested respond to the stimuli?'])}',
                        '{self.handle_response_time(entry_dict['Did the lifeguard being vigilance tested respond to the stimuli?'])}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"VAT (ID: {entry_dict['Unique ID']}) already in table 'vats'")
            else:
                logging.log(msg=f"VAT (ID: {entry_dict['Unique ID']}) inserted into table 'vats'", level=logging.INFO)
        elif table == "opening_checklists":
            keys = entry_dict.keys()
            oc_uuid = entry_dict['Unique ID']
            discord_id = self.handle_names('007', entry_dict['Name of the individual completing the inspection']) if self.handle_names('007', entry_dict['Name of the individual completing the inspection']) else 'NULL'
            name = self.handle_quotes(entry_dict['Name of the individual completing the inspection'])
            branch_id = '007'
            regulatory_info = self.handle_quotes(entry_dict[self.get_regulatory_key_from_rss_keys(keys)]) if self.get_regulatory_key_from_rss_keys(keys) else 'NULL'
            pool = entry_dict['Which pool do you need to inspect?'] if 'Which pool do you need to inspect?' in keys else 'NULL'
            opening_time = self.handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(entry_dict['Date & Time of Inspection']) if 'Date & Time of Inspection' in keys else 'NULL'
            submit_time = entry_dict['Time']
            aed_info = entry_dict['AED Inspection'] if 'AED Inspection' in keys else 'NULL'
            adult_pads_expiration_date = self.handle_rss_date(entry_dict['What is the expiration date for the Adult Electrode Pads?']) if 'What is the expiration date for the Adult Electrode Pads?' in keys else 'NULL'
            pediatric_pads_expiration_date = self.handle_rss_date(entry_dict['What is the expiration date for the Pediatric Electrode Pads?']) if 'What is the expiration date for the Pediatric Electrode Pads?' in keys else 'NULL'
            aspirin_expiration_date = self.handle_rss_date(entry_dict['What is the expiration date of the Aspirin?']) if 'What is the expiration date of the Aspirin?' in keys else 'NULL'
            sup_oxygen_info = entry_dict['Supplemental Oxygen Inspection'] if 'Supplemental Oxygen Inspection' in keys else 'NULL'
            sup_oxygen_psi = int(entry_dict['What is the current pressure level of the oxygen tank?'].split(" ")[1]) if 'What is the current pressure level of the oxygen tank?' in keys else 'NULL'
            first_aid_info = entry_dict['First Aid Kit Inspection'] if 'First Aid Kit Inspection' in keys else 'NULL'
            chlorine = entry_dict['What is the opening CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the opening CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            ph = entry_dict['What is the opening PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the opening PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            water_temp = entry_dict['What is the opening water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the opening water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            lights_function = 'NULL'
            handicap_chair_function = entry_dict['Does the handicap chair function as required for usage by guests?'] if 'Does the handicap chair function as required for usage by guests?' in keys else 'NULL'
            spare_battery_present = entry_dict['Is there a spare battery available for the handicap chair?'] if 'Is there a spare battery available for the handicap chair?' in keys else 'NULL'
            vacuum_present = entry_dict['Did you have to remove the robotic vacuum from the pool before opening?'] if 'Did you have to remove the robotic vacuum from the pool before opening?' in keys else 'NULL'
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO {table}
                    VALUES(
                        {oc_uuid}, {discord_id}, '{name}', '{branch_id}', '{pool}', '{opening_time}', '{submit_time}', '{regulatory_info}',
                        '{aed_info}', '{adult_pads_expiration_date}', '{pediatric_pads_expiration_date}', '{aspirin_expiration_date}',
                        '{sup_oxygen_info}', '{sup_oxygen_psi}', '{first_aid_info}', '{chlorine}', '{ph}', '{water_temp}',
                        '{lights_function}', '{handicap_chair_function}', '{spare_battery_present}', '{vacuum_present}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"Opening Checklist (ID: {entry_dict['Unique ID']}) already in table 'opening_checklists'")
            except sqlite3.OperationalError:
                logging.warning(f"Opening Checklist (ID: {entry_dict['Unique ID']}) error adding to table 'opening_checklists'")
            else:
                logging.log(msg=f"Opening Checklist (ID: {entry_dict['Unique ID']}) inserted into table 'opening_checklists'", level=logging.INFO)
        elif table == "closing_checklists":
            keys = entry_dict.keys()
            oc_uuid = entry_dict['Unique ID']
            discord_id = self.handle_names('007', entry_dict['Name of the individual completing the inspection']) if self.handle_names('007', entry_dict['Name of the individual completing the inspection']) else 'NULL'
            name = self.handle_quotes(entry_dict['Name of the individual completing the inspection'])
            branch_id = '007'
            pool = entry_dict['Which pool do you need to inspect?'] if 'Which pool do you need to inspect?' in keys else 'NULL'
            closing_time = self.handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(entry_dict['Date & Time of Inspection']) if 'Date & Time of Inspection' in keys else 'NULL'
            submit_time = entry_dict['Time']
            regulatory_info = self.handle_quotes(entry_dict[self.get_regulatory_key_from_rss_keys(keys)]) if self.get_regulatory_key_from_rss_keys(keys) else 'NULL'
            chlorine = entry_dict['What is the closing CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the closing CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            ph = entry_dict['What is the closing PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the closing PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            water_temp = entry_dict['What is the closing water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?'] if 'What is the closing water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?' in keys else 'NULL'
            lights_function = 'NULL'
            vacuum_function = self.handle_vacuum_closing(entry_dict)
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO {table}
                    VALUES(
                        {oc_uuid}, {discord_id}, '{name}', '{branch_id}', '{pool}', '{closing_time}', '{submit_time}', '{regulatory_info}',
                        '{chlorine}', '{ph}', '{water_temp}', '{lights_function}', '{vacuum_function}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"Closing Checklist (ID: {entry_dict['Unique ID']}) already in table 'closing_checklists'")
            except sqlite3.OperationalError:
                logging.warning(f"Closing Checklist (ID: {entry_dict['Unique ID']}) error adding to table 'closing_checklists'")
            else:
                logging.log(msg=f"Closing Checklist (ID: {entry_dict['Unique ID']}) inserted into table 'closing_checklists'", level=logging.INFO)\

    def init_tables(self):
        cursor = self.connection.cursor()
        with open('migrations/01_INIT.sql') as file:
            init_sql = file.read()
        cursor.executescript(init_sql)

    def init_branches(self):
        cursor = self.connection.cursor()
        for branch_id, branch_info in settings.SETTINGS_DICT['branches'].items():
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO branches
                    VALUES(
                        '{branch_id}',
                        '{branch_info['name']}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"Branch (ID: {branch_id}) already in table 'branches'")
            else:
                logging.log(msg=f"Branch (ID: {branch_id}) inserted into table 'branches'", level=logging.INFO)

    def check_w2w_connection(self, branch_id, branch_info):
        try:
            req = requests.get(f"https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key={branch_info['w2w_token']}")
        except KeyError:
            logging.warning(f"Branch (ID: {branch_id}) does not have W2W connected.")
            return None
        else:
            return req.json()

    def init_w2w_users(self, branch_id):
        cursor = self.connection.cursor()
        req_json = self.check_w2w_connection(branch_id, settings.SETTINGS_DICT['branches'][branch_id])
        if req_json:
            for employee in req_json['EmployeeList']:
                self.w2w_users[branch_id].append(employee)
                discord_id = self.handle_names(branch_id, employee['FIRST_NAME'], employee['LAST_NAME'])
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO w2w_users
                        VALUES(
                            {employee['W2W_EMPLOYEE_ID']},
                            {discord_id if discord_id else 'NULL'},
                            '{employee['FIRST_NAME']}',
                            '{employee['LAST_NAME']}',
                            '{branch_id if branch_id else 'NULL'}',
                            '{self.handle_emails(employee['EMAILS'])}',
                            '{employee['CUSTOM_2']}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.warning(f"W2W Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (ID: {employee['W2W_EMPLOYEE_ID']}) already in table 'w2w_users'")
                else:
                    logging.log(msg=f"W2W Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (ID: {employee['W2W_EMPLOYEE_ID']}) inserted into table 'w2w_users'", level=logging.INFO)
    
    def init_discord_users(self, users: List, branch_id: str) -> None:
        cursor = self.connection.cursor()
        for user in users:
            self.discord_users[branch_id].append(user)
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO discord_users
                    VALUES(
                        {user.id},
                        '{user.name}',
                        '{user.display_name}',
                        '{branch_id}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                pass
                #logging.warning(f"Discord User {user.display_name} (ID: {user.id}) already in table 'discord_users'")
            else:
                pass
                #logging.log(msg=f"Discord User {user.display_name} (ID: {user.id}) inserted into table 'discord_users'", level=logging.INFO)

    def select_discord_users(self, users: List):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT discord_users.id FROM discord_users
                INNER JOIN w2w_users
                ON discord_users.id = w2w_users.discord_id
                WHERE w2w_users.id IN ({','.join(str(id) for id in users)})
            """)
        except Exception as e:
            print(e)
        else:
            selected_users = []
            for user in cursor.fetchall():
                selected_users.append(user[0])
            return selected_users
        
    def get_regulatory_key_from_rss_keys(self, keys: list):
        for key in keys:
            if 'Regulatory' in key:
                return key
        return None

    def handle_vacuum_closing(self, entry_dict: dict):
        if entry_dict['Does your supervisor expect you to place a robotic vacuum into the pool?'] == 'Yes':
            if entry_dict['Have you placed the robotic vacuum in the pool?'] == 'Yes':
                if entry_dict['Before leaving the Y, do you see the vacuum moving across the pool bottom as expected?'] == 'Yes':
                    return 'Yes'
        else:
            return 'No'

    def handle_emails(self, emails: str) -> str:
        if "," not in emails:
            return emails
        else:
            return emails.split(",")[0]
    
    def handle_names(self, branch_id: str, name: str, last_name: str = None) -> str:
        if not last_name:
            name, last_name = name.split(' ', 1)
        potential_match = (0, 0)
        for discord_user in self.discord_users[branch_id]:
            discord_display_name_split = discord_user.display_name.lower().split(' ', 1)
            last_name_match = SequenceMatcher(None, discord_display_name_split[-1], last_name.lower()).ratio()
            first_name_match = SequenceMatcher(None, discord_display_name_split[0], name.lower()).ratio()
            if last_name_match > 0.85 and first_name_match > potential_match[1]:
                potential_match = (discord_user.id, first_name_match)
        return potential_match[0]
    
    def handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%B %d, %Y %I:%M %p')
    
    def handle_rss_datetime(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%b %d, %Y %I:%M %p')
    
    def handle_rss_date(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%b %d, %Y')

    def handle_formstack_datetime(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S')
    
    def handle_num_of_guests(self, guests_string: str):
        guests_list = guests_string.split(' ')
        try:
            return int(guests_list[-2])
        except ValueError as e:
            logging.warning(f"Error: Number of Guests field improperly filled out on Formstack {e}")
            return 10
          
    def handle_num_of_guards(self, guards_string: str):
        if guards_string == 'Yes':
            return 1
        else:
            guards_list = guards_string.split(' ')
            return int(guards_list[3])
        
    def handle_depth(self, depth_string: str):
        if depth_string == 'Less than 1 Foot of Water':
            return 0.5
        if depth_string == '12 Feet or Greater':
            return 12.0
        else:
            depth_list = depth_string.split(' ')
            depth_list = depth_list[0].split('-')
            return (float(depth_list[0]) + float(depth_list[1])) / 2
        
    def handle_pass(self, pass_string: str):
        if pass_string == 'Yes (10 seconds or less)':
            return 'True'
        else:
            return 'False'
        
    def handle_response_time(self, pass_string: str):
        if pass_string == 'Yes (10 seconds or less)':
            return 10.0
        elif 'seconds' in pass_string:
            pass_list = pass_string.split(' ')
            return (float(pass_list[1][1:]) + float(pass_list[3])) / 2
        else:
            return 60.0
        
    def handle_quotes(self, name: str):
        if "'" in name:
            return "''".join(name.split("'"))
        else:
            return name
        
    def handle_branch(self, branch: str):
        return '007'

    def load_chems(self) -> None:
        print("load chems")
        cursor = self.connection.cursor()
        with open('chems.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                discord_id = self.handle_names('007', row['Your Name (First)'], row['Your Name (Last)'])
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO chem_checks
                        VALUES(
                            {row['Unique ID']},
                            {discord_id if discord_id else 'NULL'},
                            '{self.handle_quotes(row['Your Name (First)']).strip()} {self.handle_quotes(row['Your Name (Last)']).strip()}',
                            '{self.handle_branch(row['Branch'])}',
                            '{row['Western']}',
                            '{row['Location of Water Sample, Western']}',
                            '{self.handle_rss_datetime(row['Date/Time'])}',
                            '{self.handle_formstack_datetime(row['Time'])}',
                            {row['Chlorine']},
                            {row['PH']},
                            '{row['Water Temperature']}',
                            '{row['Total Number of Swimmers']}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.warning(f"Chem Check (ID: {row['Unique ID']}) already in table 'chem_checks'")
                    self.form_tables['chem_checks']['last_id'] = int(row['Unique ID'])
                else:
                    logging.log(msg=f"Chem Check (ID: {row['Unique ID']}) inserted into table 'chem_checks'", level=logging.INFO)
                    self.form_tables['chem_checks']['last_id'] = int(row['Unique ID'])
    
    def load_vats(self) -> None:
        print("load vats")
        cursor = self.connection.cursor()
        with open('vats.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                guard_discord_id = self.handle_names(
                    '007',
                    row['Name of Lifeguard Vigilance Tested (First)'],
                    row['Name of Lifeguard Vigilance Tested (Last)']
                )
                sup_discord_id = self.handle_names(
                    '007',
                    row['Who monitored & conducted the vigilance test? (First)'],
                    row['Who monitored & conducted the vigilance test? (Last)']
                )
                if row['Which Pool? - Western']:
                    pool = row['Which Pool? - Western']
                else:
                    pool = row['Which Pool? ']
                if row['Date & Time of Vigilance Test Conducted']:
                    vat_datetime = datetime.datetime.strptime(row['Date & Time of Vigilance Test Conducted'],
                        '%B %d, %Y %H:%M %p')
                else:
                    vat_datetime = datetime.datetime.strptime(
                        f"{row['Date of Vigilance Test Conducted']} {row['Time of Vigilance Test Conducted ']}",
                        '%b %d, %Y %H:%M %p'
                    )
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO vats
                        VALUES(
                            {row['Unique ID']},
                            {guard_discord_id if guard_discord_id else 'NULL'},
                            '{self.handle_quotes(row['Name of Lifeguard Vigilance Tested (First)']).strip()} {self.handle_quotes(row['Name of Lifeguard Vigilance Tested (Last)']).strip()}',
                            {sup_discord_id if sup_discord_id else 'NULL'},
                            '{self.handle_quotes(row['Who monitored & conducted the vigilance test? (First)']).strip()} {self.handle_quotes(row['Who monitored & conducted the vigilance test? (Last)']).strip()}',
                            '{self.handle_branch(row['YMCA of Delaware Branch'])}',
                            '{pool}',
                            '{vat_datetime}',
                            '{self.handle_formstack_datetime(row['Time'])}',
                            '{self.handle_num_of_guests(row['How many guests do you believe were in the pool?'])}',
                            '{self.handle_num_of_guards(row['Were they the only lifeguard watching the pool?'])}',
                            '{row['What type of stimuli was used?']}',
                            '{self.handle_depth(row['What was the water depth where the stimuli was placed?'])}',
                            '{self.handle_pass(row['Did the lifeguard being vigilance tested respond to the stimuli?'])}',
                            '{self.handle_response_time(row['Did the lifeguard being vigilance tested respond to the stimuli?'])}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.warning(f"VAT (ID: {row['Unique ID']}) already in table 'vats'")
                    self.form_tables['vats']['last_id'] = int(row['Unique ID'])
                else:
                    logging.log(msg=f"VAT (ID: {row['Unique ID']}) inserted into table 'vats'", level=logging.INFO)
                    self.form_tables['vats']['last_id'] = int(row['Unique ID'])

    def select_last_chem(self, pools: List[str], branch_id: str):
        cursor = self.connection.cursor()
        chems = []
        for pool in pools:
            try:
                cursor.execute(f"""
                    SELECT discord_id, chem_uuid, pool, chlorine, ph, water_temp, num_of_swimmers, MAX(sample_time)
                    FROM chem_checks
                    WHERE pool = '{pool}' AND branch_id = '{branch_id}';
                """)
            except Exception as e:
                print(e)
            else:
                chems.append(cursor.fetchone())
        return chems
    
    def pool_to_opening_type(self, pool: str):
        if pool == 'Complex Lap Pool':
            return 'Bubble Pool'
        elif pool == 'Complex Family Pool':
            return 'Outdoor Complex'
        else:
            return pool
    
    def select_last_opening(self, pool: str, branch_id: str):
        cursor = self.connection.cursor()
        oc_pool = self.pool_to_opening_type(pool)
        chems = []
        try:
            cursor.execute(f"""
                SELECT discord_id, oc_uuid, pool, sup_oxygen_psi, chlorine, ph, water_temp, MAX(submit_time)
                FROM opening_checklists
                WHERE pool = '{oc_pool}' AND branch_id = '{branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchone()

    def select_last_vat(self, branch_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT guard_discord_id, sup_discord_id, vat_uuid, pool, num_of_swimmers, num_of_guards, stimuli, pass, response_time, MAX(vat_time)
                FROM vats
                WHERE branch_id = '{branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return [cursor.fetchone()]
        
    def select_vats_month(self, dt_now: datetime.datetime, branch_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT guard_discord_id, sup_discord_id, vat_uuid, pool, num_of_swimmers, num_of_guards, stimuli, pass, response_time, vat_time
                FROM vats
                WHERE vat_time > '{datetime.datetime(dt_now.year, dt_now.month, 1)}' AND branch_id = '{branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchall()
# if __name__ == "__main__":
#     run()
#a = YMCADatabase()
# print(a.select_discord_users([731933785, 568705929, 757270967, 564685546]))
#a = YMCADatabase()
# a.load_chems()
# formstack_time = '2020-06-10 07:05:47'
# print(datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S'))
#print(a.select_vats_month(datetime.datetime.now()))
#print(SequenceMatcher(None, 'christian', 'chris').ratio())