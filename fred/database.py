from __future__ import annotations

import sqlite3
import logging
import datetime
import csv
from typing import TYPE_CHECKING, List, Union
from difflib import SequenceMatcher
import fred.rss as rss
import discord

if TYPE_CHECKING:
    from .ymca import YMCA
    from .branch import Branch
    from .pool_group import PoolGroup
    from .pool import Pool
    import whentowork

log = logging.getLogger()

class YMCADatabase(object):
    def __init__(self, ymca: YMCA):
        self.ymca: YMCA = ymca
        self.connection: sqlite3.Connection = None
        try:
            self.connection = sqlite3.connect("ymca_aquatics.db")
        except Exception as e:
            log.log(logging.WARN, f"Error: Connection to database 'ymca_aquatics.db' not established. {e}")
        else:
            log.log(logging.INFO, "Connection to database 'ymca_aquatics.db' established.")

    def init_database(self):
        self.init_tables()

    def init_tables(self):
        cursor = self.connection.cursor()
        with open('fred/migrations/01_INIT.sql') as file:
            init_sql = file.read()
        try:
            cursor.executescript(init_sql)
        except Exception as e:
            log.log(logging.WARN, f"Error: Could not initialize database. {e}")

    def init_database_from_branch(self, branch: Branch):
        self.init_branches(branch)
        self.init_discord_users(branch)
        self.init_w2w_users(branch)
        self.load_chems(branch)
        self.load_vats(branch)

    def init_branches(self, branch: Branch):
        cursor = self.connection.cursor()
        try:
            cursor.executescript(f"""
                BEGIN;
                INSERT INTO branches
                VALUES('{branch.branch_id}', '{branch.name}');
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            log.log(logging.WARN, f"Branch {branch.name} (ID: {branch.branch_id}) already in table 'branches'")
        else:
            log.log(logging.INFO, f"Branch {branch.name} (ID: {branch.branch_id}) inserted into table 'branches'")
        finally:
            self.init_pool_groups(branch)
    
    def init_pool_groups(self, branch: Branch):
        cursor = self.connection.cursor()
        for pool_group in branch.pool_groups:
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO pool_groups
                    VALUES('{pool_group.pool_group_id}', '{pool_group.branch_id}',
                    '{pool_group.name}');
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                log.log(logging.WARN, f"Pool Group {pool_group.name} (ID: {pool_group.pool_group_id}) already in table 'pool_groups'")
            except Exception as e:
                log.log(logging.WARN, f"Error adding Pool Group: {e}")
            else:
                log.log(logging.INFO, f"Pool Group {pool_group.name} (ID: {pool_group.pool_group_id}) inserted into table 'pool_groups'")
            finally:
                self.init_pools(pool_group)

    def init_pools(self, pool_group: PoolGroup):
        cursor = self.connection.cursor()
        for pool in pool_group.pools:
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO pools
                    VALUES('{pool.pool_id}', '{pool.branch_id}', '{pool.pool_group_id}',
                    '{pool.name}');
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                log.log(logging.WARN, f"Pool {pool.name} (ID: {pool.pool_id}) already in table 'pools'")
            except Exception as e:
                log.log(logging.WARN, f"Error adding Pool: {e}")
            else:
                log.log(logging.INFO, f"Pool {pool.name} (ID: {pool.pool_id}) inserted into table 'pools'")

    def init_discord_users(self, branch: Branch) -> None:
        cursor = self.connection.cursor()
        for user in branch.guild.members:
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO discord_users
                    VALUES(
                        {user.id},
                        '{user.name}',
                        '{user.display_name}',
                        '{branch.branch_id}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                log.log(logging.WARN, f"Discord User {user.display_name} (ID: {user.id}) already in table 'discord_users'")
            else:
                log.log(logging.DEBUG, f"Discord User {user.display_name} (ID: {user.id}) inserted into table 'discord_users'")

    def init_w2w_users(self, branch: Branch):
        cursor = self.connection.cursor()
        for employee in branch.w2w_client.employees:
            discord_id = self.match_discord_id(branch, employee.first_name, employee.last_name)
            discord_id = discord_id if discord_id else 'NULL'
            email = employee.emails[0] if employee.emails else 'NULL'
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO w2w_users
                    VALUES(
                        {employee.w2w_employee_id},
                        {discord_id},
                        '{employee.first_name}',
                        '{employee.last_name}',
                        '{branch.branch_id}',
                        '{email}',
                        '{employee.custom_field_2}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                log.log(logging.WARN, f"W2W Employee {employee.first_name} {employee.last_name} (ID: {employee.w2w_employee_id}) already in table 'w2w_users'")
            else:
                log.log(logging.INFO, f"W2W Employee {employee.first_name} {employee.last_name} (ID: {employee.w2w_employee_id}) inserted into table 'w2w_users'")

    def match_discord_id(self, branch: Branch, name: str, last_name: str = None) -> int:
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
        return potential_match[0]
    
    def match_pool_id(self, branch: Branch, pool_alias: str) -> str:
        for pool_group in branch.pool_groups:
            for pool in pool_group.pools:
                if pool_alias in pool.aliases:
                    return pool.pool_id
        return 'NULL'

    def load_chems(self, branch: Branch) -> None:
        cursor = self.connection.cursor()
        with open('fred/data/chems.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                chem_uuid = int(row['Unique ID'])
                discord_id = self.match_discord_id(branch, row['Your Name (First)'], row['Your Name (Last)'])
                discord_id = discord_id if discord_id else 'NULL'
                name = f"{self.handle_quotes(row['Your Name (First)']).strip()} {self.handle_quotes(row['Your Name (Last)']).strip()}"
                pool_id = self.match_pool_id(branch, row.get('Western', ''))                
                sample_location = row.get('Location of Water Sample, Western', 'NULL')
                sample_time = self.handle_rss_datetime(row['Date/Time'])
                submit_time = self.handle_formstack_datetime(row['Time'])
                chlorine = row['Chlorine']
                ph = row['PH']
                water_temp = row['Water Temperature']
                num_of_swimmers = row['Total Number of Swimmers']
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO chem_checks
                        VALUES(
                            {chem_uuid}, {discord_id}, '{name}', '{branch.branch_id}',
                            '{pool_id}', '{sample_location}', '{sample_time}',
                            '{submit_time}', {chlorine}, {ph}, '{water_temp}',
                            '{num_of_swimmers}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    log.log(logging.WARN, f"Chem Check (ID: {chem_uuid}) already in table 'chem_checks'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting Chem Check (ID: {chem_uuid}). Error: {e}")
                else:
                    log.log(logging.INFO, f"Chem Check (ID: {chem_uuid}) inserted into table 'chem_checks'")
                    branch.last_chem_id = chem_uuid

    def load_vats(self, branch: Branch) -> None:
        cursor = self.connection.cursor()
        with open('fred/data/vats.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                vat_uuid = int(row['Unique ID'])
                guard_discord_id = self.match_discord_id(
                    branch,
                    row['Name of Lifeguard Vigilance Tested (First)'],
                    row['Name of Lifeguard Vigilance Tested (Last)']
                )
                guard_discord_id = guard_discord_id if guard_discord_id else 'NULL'
                guard_name = f"{self.handle_quotes(row['Name of Lifeguard Vigilance Tested (First)']).strip()} {self.handle_quotes(row['Name of Lifeguard Vigilance Tested (Last)']).strip()}"
                sup_discord_id = self.match_discord_id(
                    branch,
                    row['Who monitored & conducted the vigilance test? (First)'],
                    row['Who monitored & conducted the vigilance test? (Last)']
                )
                sup_discord_id = sup_discord_id if sup_discord_id else 'NULL'
                sup_name = f"{self.handle_quotes(row['Who monitored & conducted the vigilance test? (First)']).strip()} {self.handle_quotes(row['Who monitored & conducted the vigilance test? (Last)']).strip()}"
                if row['Which Pool? - Western']:
                    pool_id = self.match_pool_id(branch, row['Which Pool? - Western'])
                else:
                    pool_id = self.match_pool_id(branch, row['Which Pool? '])
                if row['Date & Time of Vigilance Test Conducted']:
                    vat_datetime = datetime.datetime.strptime(row['Date & Time of Vigilance Test Conducted'],
                        '%B %d, %Y %H:%M %p')
                else:
                    vat_datetime = datetime.datetime.strptime(
                        f"{row['Date of Vigilance Test Conducted']} {row['Time of Vigilance Test Conducted ']}",
                        '%b %d, %Y %H:%M %p'
                    )
                submit_time = self.handle_formstack_datetime(row['Time'])
                num_of_guests = self.handle_num_of_guests(row['How many guests do you believe were in the pool?'])
                num_of_guards = self.handle_num_of_guards(row['Were they the only lifeguard watching the pool?'])
                stimuli = row['What type of stimuli was used?']
                depth = self.handle_depth(row['What was the water depth where the stimuli was placed?'])
                vat_pass = self.handle_pass(row['Did the lifeguard being vigilance tested respond to the stimuli?'])
                response_time = self.handle_response_time(row['Did the lifeguard being vigilance tested respond to the stimuli?'])
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO vats
                        VALUES(
                            {vat_uuid}, {guard_discord_id}, '{guard_name}',
                            {sup_discord_id}, '{sup_name}', '{branch.branch_id}',
                            '{pool_id}', '{vat_datetime}', '{submit_time}',
                            '{num_of_guests}', '{num_of_guards}', '{stimuli}',
                            '{depth}', '{vat_pass}', '{response_time}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.log(logging.WARN, f"VAT (ID: {row['Unique ID']}) already in table 'vats'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting VAT (ID: {vat_uuid}). Error: {e}")
                else:
                    logging.log(logging.INFO, f"VAT (ID: {row['Unique ID']}) inserted into table 'vats'")
                    branch.last_vat_id = vat_uuid

    def update_rss(self, branch: Branch):
        self.update_chems_rss(branch)
        self.update_vats_rss(branch)
        self.update_opening_rss(branch)
        self.update_closing_rss(branch)

    def update_chems_rss(self, branch: Branch):
        num_of_updates = 0
        chems_rss = rss.form_rss_to_dict(branch.rss_links['chems'])
        cursor = self.connection.cursor()
        for entry in chems_rss:
            if entry['Unique ID'] > branch.last_chem_id:
                chem_uuid = entry['Unique ID']
                discord_id = self.match_discord_id(branch, entry['Your Name'])
                discord_id = discord_id if discord_id else 'NULL'
                name = self.handle_quotes(entry['Your Name'])
                pool_id = self.match_pool_id(branch, entry['Western'])
                sample_location = entry['Location of Water Sample, Western']
                sample_time = self.handle_rss_datetime(entry['Date/Time'])
                submit_time = entry['Time']
                chlorine = entry['Chlorine']
                ph = entry['PH']
                water_temp = entry['Water Temperature']
                num_of_swimmers = entry['Total Number of Swimmers'].strip()
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO chem_checks
                        VALUES(
                            {chem_uuid}, {discord_id}, '{name}', '{branch.branch_id}',
                            '{pool_id}', '{sample_location}', '{sample_time}',
                            '{submit_time}', {chlorine}, {ph}, '{water_temp}',
                            '{num_of_swimmers}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.warning(f"Chem Check (ID: {entry['Unique ID']}) already in table 'chem_checks'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting Chem Check (ID: {chem_uuid}). Error: {e}")
                else:
                    logging.log(msg=f"Chem Check (ID: {entry['Unique ID']}) inserted into table 'chem_checks'", level=logging.INFO)
                    num_of_updates += 1
                    branch.last_chem_id = entry['Unique ID']
        return num_of_updates
    
    def update_vats_rss(self, branch: Branch):
        num_of_updates = 0
        vats_rss = rss.form_rss_to_dict(branch.rss_links['vats'])
        cursor = self.connection.cursor()
        for entry in vats_rss:
            if entry['Unique ID'] > branch.last_vat_id:
                vat_uuid = entry['Unique ID']
                guard_discord_id = self.match_discord_id(branch, entry['Name of Lifeguard Vigilance Tested'])
                guard_discord_id = guard_discord_id if guard_discord_id else 'NULL'
                guard_name = self.handle_quotes(entry['Name of Lifeguard Vigilance Tested'])
                sup_discord_id = self.match_discord_id(branch, entry['Who monitored & conducted the vigilance test?'])
                sup_discord_id = sup_discord_id if sup_discord_id else 'NULL'
                sup_name = self.handle_quotes(entry['Who monitored & conducted the vigilance test?'])
                pool_id = self.match_pool_id(branch, entry['Which Pool? '])
                vat_time = self.handle_rss_datetime(f"{entry['Date of Vigilance Test Conducted']} {entry['Time of Vigilance Test Conducted ']}")
                submit_time = entry['Time']
                num_of_swimmers = self.handle_num_of_guests(entry['How many guests do you believe were in the pool?'])
                num_of_guards = self.handle_num_of_guards(entry['Were they the only lifeguard watching the pool?'])
                stimuli = entry['What type of stimuli was used?']
                depth = self.handle_depth(entry['What was the water depth where the stimuli was placed?'])
                vat_pass = self.handle_pass(entry['Did the lifeguard being vigilance tested respond to the stimuli?'])
                response_time = self.handle_response_time(entry['Did the lifeguard being vigilance tested respond to the stimuli?'])
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO vats
                        VALUES(
                            {vat_uuid}, {guard_discord_id}, '{guard_name}', '{sup_discord_id}', '{sup_name}', 
                            '{branch.branch_id}', '{pool_id}', '{vat_time}', '{submit_time}', '{num_of_swimmers}',
                            '{num_of_guards}', '{stimuli}', {depth}, '{vat_pass}', '{response_time}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.warning(f"VAT (ID: {entry['Unique ID']}) already in table 'vats'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting VAT (ID: {vat_uuid}). Error: {e}")
                else:
                    logging.log(msg=f"VAT (ID: {entry['Unique ID']}) inserted into table 'vats'", level=logging.INFO)
                    num_of_updates += 1
                    branch.last_vat_id = entry['Unique ID']                   
        return num_of_updates
    
    def update_opening_rss(self, branch: Branch):
        num_of_updates = 0
        opening_rss = rss.form_rss_to_dict(branch.rss_links['oc'])
        opening_rss: List[dict] = list(filter(lambda entry: entry['What checklist do you need to submit?'] == 'Opening Checklist', opening_rss))
        cursor = self.connection.cursor()
        for entry in opening_rss:
            if entry['Unique ID'] > branch.last_opening_id:
                keys = entry.keys()
                oc_uuid = entry['Unique ID']
                discord_id = self.match_discord_id(branch, entry['Name of the individual completing the inspection'])
                discord_id = discord_id if discord_id else 'NULL'
                name = self.handle_quotes(entry['Name of the individual completing the inspection'])
                regulatory_info = self.handle_quotes(entry[self.get_regulatory_key_from_rss_keys(keys)]) if self.get_regulatory_key_from_rss_keys(keys) else 'NULL'
                checklist_group = entry.get('Which pool do you need to inspect?', 'NULL')
                opening_time = self.handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(entry['Date & Time of Inspection']) if 'Date & Time of Inspection' in keys else 'NULL'
                submit_time = entry['Time']
                aed_info = entry.get('AED Inspection', 'NULL')
                adult_pads_expiration_date = self.handle_rss_date(entry['What is the expiration date for the Adult Electrode Pads?']) if 'What is the expiration date for the Adult Electrode Pads?' in keys else 'NULL'
                pediatric_pads_expiration_date = self.handle_rss_date(entry['What is the expiration date for the Pediatric Electrode Pads?']) if 'What is the expiration date for the Pediatric Electrode Pads?' in keys else 'NULL'
                aspirin_expiration_date = self.handle_rss_date(entry['What is the expiration date of the Aspirin?']) if 'What is the expiration date of the Aspirin?' in keys else 'NULL'
                sup_oxygen_info = entry.get('Supplemental Oxygen Inspection', 'NULL')
                sup_oxygen_psi = int(entry['What is the current pressure level of the oxygen tank?'].split(" ")[1]) if 'What is the current pressure level of the oxygen tank?' in keys else 'NULL'
                first_aid_info = entry.get('First Aid Kit Inspection', 'NULL')
                chlorine = entry.get('What is the opening CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                ph = entry.get('What is the opening PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                water_temp = entry.get('What is the opening water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                lights_function = 'NULL'
                handicap_chair_function = entry.get('Does the handicap chair function as required for usage by guests?', 'NULL')
                spare_battery_present = entry.get('Is there a spare battery available for the handicap chair?', 'NULL')
                vacuum_present = entry.get('Did you have to remove the robotic vacuum from the pool before opening?', 'NULL')
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO opening_checklists
                        VALUES(
                            {oc_uuid}, {discord_id}, '{name}', '{branch.branch_id}', '{checklist_group}', '{opening_time}', '{submit_time}', '{regulatory_info}',
                            '{aed_info}', '{adult_pads_expiration_date}', '{pediatric_pads_expiration_date}', '{aspirin_expiration_date}',
                            '{sup_oxygen_info}', '{sup_oxygen_psi}', '{first_aid_info}', '{chlorine}', '{ph}', '{water_temp}',
                            '{lights_function}', '{handicap_chair_function}', '{spare_battery_present}', '{vacuum_present}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.log(logging.WARN, f"Opening Checklist (ID: {entry['Unique ID']}) already in table 'opening_checklists'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting Opening Checklist (ID: {oc_uuid}). Error: {e}")
                else:
                    logging.log(logging.INFO, f"Opening Checklist (ID: {entry['Unique ID']}) inserted into table 'opening_checklists'")
                    num_of_updates += 1
                    branch.last_opening_id = entry['Unique ID']
        return num_of_updates
    
    def update_closing_rss(self, branch: Branch):
        num_of_updates = 0
        closing_rss = rss.form_rss_to_dict(branch.rss_links['oc'])
        closing_rss: List[dict] = list(filter(lambda entry: entry['What checklist do you need to submit?'] == 'Closing Checklist', closing_rss))
        cursor = self.connection.cursor()
        for entry in closing_rss:
            if entry['Unique ID'] > branch.last_closing_id:
                keys = entry.keys()
                oc_uuid = entry['Unique ID']
                discord_id = self.match_discord_id(branch, entry['Name of the individual completing the inspection'])
                discord_id = discord_id if discord_id else 'NULL'
                name = self.handle_quotes(entry['Name of the individual completing the inspection'])
                checklist_group = entry.get('Which pool do you need to inspect?', 'NULL')
                closing_time = self.handle_rss_datetime_oc_because_consistency_apparently_doesnt_exist(entry['Date & Time of Inspection']) if 'Date & Time of Inspection' in keys else 'NULL'
                submit_time = entry['Time']
                regulatory_info = self.handle_quotes(entry[self.get_regulatory_key_from_rss_keys(keys)]) if self.get_regulatory_key_from_rss_keys(keys) else 'NULL'
                chlorine = entry.get('What is the closing CL reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                ph = entry.get('What is the closing PH reading (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                water_temp = entry.get('What is the closing water temperature (Indoor Pool, Bubble Pool, 10-Lane Pool, Outdoor Complex Lap Pool)?', 'NULL')
                lights_function = 'NULL'
                vacuum_function = self.handle_vacuum_closing(entry)
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO closing_checklists
                        VALUES(
                            {oc_uuid}, {discord_id}, '{name}', '{branch.branch_id}', '{checklist_group}', '{closing_time}', '{submit_time}', '{regulatory_info}',
                            '{chlorine}', '{ph}', '{water_temp}', '{lights_function}', '{vacuum_function}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    logging.log(logging.WARN, f"Closing Checklist (ID: {entry['Unique ID']}) already in table 'closing_checklists'")
                except Exception as e:
                    log.log(logging.ERROR, f"Issue inserting Closing Checklist (ID: {oc_uuid}). Error: {e}")
                else:
                    logging.log(logging.INFO, f"Closing Checklist (ID: {entry['Unique ID']}) inserted into table 'closing_checklists'")
                    num_of_updates += 1
                    branch.last_closing_id = entry['Unique ID']
        return num_of_updates
     
    def get_regulatory_key_from_rss_keys(self, keys: list):
        for key in keys:
            if 'Regulatory' in key:
                return key
        return None

    def handle_vacuum_closing(self, entry: dict):
        if entry.get('Does your supervisor expect you to place a robotic vacuum into the pool?') == 'Yes':
            if entry.get('Have you placed the robotic vacuum in the pool?') == 'Yes':
                if entry.get('Before leaving the Y, do you see the vacuum moving across the pool bottom as expected?') == 'Yes':
                    return 'Yes'
        else:
            return 'No'
    
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







    def select_discord_user(self, employee: whentowork.Employee, branch: Branch) -> Union[discord.Member, None]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT discord_id FROM w2w_users
                WHERE id = {employee.w2w_employee_id};
            """)
        except Exception as e:
            print(e)
        else:
            user = cursor.fetchone()
            if user:
                discord_user = branch.guild.get_member(user[0])
                if discord_user:
                    return discord_user
            else:
                

    def select_last_chems(self, pools: List[Pool], branch: Branch) -> List:
        cursor = self.connection.cursor()
        chems = []
        for pool in pools:
            try:
                cursor.execute(f"""
                    SELECT 
                        chem_checks.discord_id,
                        chem_checks.chem_uuid,
                        pools.pool_id,
                        chem_checks.chlorine,
                        chem_checks.ph,
                        chem_checks.water_temp,
                        chem_checks.num_of_swimmers,
                        MAX(chem_checks.sample_time)
                    FROM chem_checks
                    LEFT JOIN pools ON vats.pool_id = pools.id
                    WHERE pool_id = '{pool.pool_id}' AND branch_id = '{branch.branch_id}';
                """)
            except Exception as e:
                print(e)
            else:
                chems.append(cursor.fetchone())
        return chems
    
    def select_last_opening(self, pool: Pool, branch: Branch):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT discord_id, oc_uuid, pool_id, sup_oxygen_psi, chlorine, ph, water_temp, MAX(submit_time)
                FROM opening_checklists
                WHERE pool_id = '{pool.pool_id}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchone()

    def select_last_vat(self, branch: Branch):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT vats.guard_discord_id, vats.sup_discord_id, vats.vat_uuid, pool.name, vats.num_of_swimmers, vats.num_of_guards, vats.stimuli, vats.pass, vats.response_time, MAX(vats.vat_time)
                FROM vats
                LEFT JOIN pools ON vats.pool_id = pools.id
                WHERE branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchone()
        
    def select_vats_month(self, dt_now: datetime.datetime, branch: Branch):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT vats.guard_discord_id, vats.sup_discord_id, vats.vat_uuid, pool.name, vats.num_of_swimmers, vats.num_of_guards, vats.stimuli, vats.pass, vats.response_time, vats.vat_time
                FROM vats
                LEFT JOIN pools ON vats.pool_id = pools.id
                WHERE vat_time > '{datetime.datetime(dt_now.year, dt_now.month, 1)}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchall()