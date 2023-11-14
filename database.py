import sqlite3
import requests
import settings
import logging
import datetime
import csv
from typing import List
from discord.user import User as DicordUser
from difflib import SequenceMatcher

class YMCADatabase(object):

    connection = None

    def __init__(self):
        if YMCADatabase.connection is None:
            try:
                YMCADatabase.connection = sqlite3.connect("ymca_aquatics.db")
            except Exception as e:
                logging.warning(f"Error: Connection to database 'ymca_aquatics.db' not established {e}")
            else:
                logging.log(msg="Connection to database 'ymca_aquatics.db' established", level=logging.INFO)
                self.w2w_users = []
                self.discord_users = []
                self.init_tables()
                self.init_w2w_users()


    def init_tables(self):
        cursor = self.connection.cursor()
        cursor.executescript("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS w2w_users(
                id PRIMARY KEY,
                first_name,
                last_name,
                email,
                cert_expiration_date
            );
            CREATE TABLE IF NOT EXISTS pectora_users(
                id PRIMARY KEY,
                first_name,
                last_name,
                email,
                cert_expiration_date
            );
            CREATE TABLE IF NOT EXISTS discord_users(
                id PRIMARY KEY, 
                username, 
                nickname,
                w2w_id,
                pectora_id,
                FOREIGN KEY(w2w_id) REFERENCES w2w_users(id),
                FOREIGN KEY(pectora_id) REFERENCES pectora_users(id)
            );
            CREATE TABLE IF NOT EXISTS chem_checks(
                chem_uuid PRIMARY KEY,
                discord_id,
                first_name,
                last_name,
                pool,
                sample_location,
                sample_time,
                submit_time, 
                chlorine,
                ph,
                water_temp,
                num_of_swimmers,
                FOREIGN KEY(discord_id) REFERENCES discord_users(id)
            );
            CREATE TABLE IF NOT EXISTS vats(
                vat_uuid PRIMARY KEY,
                guard_discord_id,
                guard_first_name,
                guard_last_name,
                sup_discord_id,
                sup_first_name,
                sup_last_name,
                pool,
                vat_time,
                submit_time,
                num_of_swimmers,
                num_of_guards,
                stimuli,
                depth,
                pass,
                response_time,
                FOREIGN KEY(guard_discord_id) REFERENCES discord_users(id),
                FOREIGN KEY(sup_discord_id) REFERENCES discord_users(id)
            );
            COMMIT;
        """)

    def init_w2w_users(self):
        cursor = self.connection.cursor()
        req = requests.get(f"https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key={settings.W2W_TOKEN}")
        req_json = req.json()
        for employee in req_json['EmployeeList']:
            self.w2w_users.append(employee)
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO w2w_users
                    VALUES(
                        {employee['W2W_EMPLOYEE_ID']},
                        '{employee['FIRST_NAME']}',
                        '{employee['LAST_NAME']}',
                        '{self.handle_emails(employee['EMAILS'])}',
                        '{employee['CUSTOM_2']}'
                    );
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                pass
                #logging.warning(f"W2W Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (ID: {employee['W2W_EMPLOYEE_ID']}) already in table 'w2w_users'")
            else:
                pass
                #logging.log(msg=f"W2W Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (ID: {employee['W2W_EMPLOYEE_ID']}) inserted into table 'w2w.users'", level=logging.INFO)
    
    def init_discord_users(self, users: List) -> None:
        cursor = self.connection.cursor()
        for user in users:
            self.discord_users.append(user)
            w2w_id = self.handle_w2w(user)
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO discord_users
                    VALUES(
                        {user.id},
                        '{user.name}',
                        '{user.display_name}',
                        {w2w_id if w2w_id else 'NULL'},
                        NULL
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
                SELECT id FROM discord_users
                WHERE w2w_id IN ({','.join(str(id) for id in users)})
            """)
        except Exception as e:
            print(e)
        else:
            selected_users = []
            for user in cursor.fetchall():
                selected_users.append(user[0])
            return selected_users


    def handle_emails(self, emails: str) -> str:
        if "," not in emails:
            return emails
        else:
            return emails.split(",")[0]
        
    def handle_w2w(self, discord_user: DicordUser) -> str:
        for w2w_user in self.w2w_users:
            w2w_name = f"{w2w_user['FIRST_NAME']} {w2w_user['LAST_NAME']}".lower()
            if SequenceMatcher(None, discord_user.display_name.lower(), w2w_name).ratio() > 0.75:
                return w2w_user['W2W_EMPLOYEE_ID']
        return None
    
    def handle_names(self, first_name: str, last_name: str) -> str:
        for discord_user in self.discord_users:
            w2w_name = f"{first_name} {last_name}".lower()
            if SequenceMatcher(None, discord_user.display_name.lower(), w2w_name).ratio() > 0.75:
                return discord_user.id
        return None

    def handle_formstack_datetime(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%m/%d/%Y %H:%M')
    
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
            return float(depth_list[0]) / float(depth_list[1])
        
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
            return float(pass_list[1][1:]) / float(pass_list[3])
        else:
            return 60.0
        
    def handle_quotes(self, name: str):
        if "'" in name:
            return "''".join(name.split("'"))
        else:
            return name

    def load_chems(self) -> None:
        print("load chems")
        cursor = self.connection.cursor()
        with open('chems_nov_9_2023.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                discord_id = self.handle_names(row['Your Name (First)'], row['Your Name (Last)'])
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO chem_checks
                        VALUES(
                            {row['Unique ID']},
                            {discord_id if discord_id else 'NULL'},
                            '{self.handle_quotes(row['Your Name (First)'])}',
                            '{self.handle_quotes(row['Your Name (Last)'])}',
                            '{row['Western']}',
                            '{row['Location of Water Sample, Western']}',
                            '{self.handle_formstack_datetime(row['Date/Time'])}',
                            '{self.handle_formstack_datetime(row['Time'])}',
                            {row['Chlorine']},
                            {row['PH']},
                            '{row['Water Temperature']}',
                            '{row['Total Number of Swimmers']}'
                        );
                        COMMIT;
                    """)
                except sqlite3.IntegrityError:
                    pass
                    logging.warning(f"Chem Check (ID: {row['Unique ID']}) already in table 'chem_checks'")
                else:
                    pass
                    logging.log(msg=f"Chem Check (ID: {row['Unique ID']}) inserted into table 'chem_checks'", level=logging.INFO)
    
    def load_vats(self) -> None:
        print("load vats")
        cursor = self.connection.cursor()
        with open('vats_nov_2023.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                guard_discord_id = self.handle_names(
                    row['Name of Lifeguard Vigilance Tested (First)'],
                    row['Name of Lifeguard Vigilance Tested (Last)']
                )
                sup_discord_id = self.handle_names(
                    row['Who monitored & conducted the vigilance test? (First)'],
                    row['Who monitored & conducted the vigilance test? (Last)']
                )
                if row['Which Pool? - Western']:
                    pool = row['Which Pool? - Western']
                else:
                    pool = row['Which Pool? ']
                if row['Date & Time of Vigilance Test Conducted']:
                    vat_datetime = self.handle_formstack_datetime(row['Date & Time of Vigilance Test Conducted'])
                else:
                    vat_datetime = datetime.datetime.strptime(
                        f"{row['Date of Vigilance Test Conducted']} {row['Time of Vigilance Test Conducted ']}",
                        '%d-%b-%y %H:%M %p'
                    )
                try:
                    cursor.executescript(f"""
                        BEGIN;
                        INSERT INTO vats
                        VALUES(
                            {row['Unique ID']},
                            {guard_discord_id if guard_discord_id else 'NULL'},
                            '{self.handle_quotes(row['Name of Lifeguard Vigilance Tested (First)'])}',
                            '{self.handle_quotes(row['Name of Lifeguard Vigilance Tested (Last)'])}',
                            {sup_discord_id if sup_discord_id else 'NULL'},
                            '{self.handle_quotes(row['Who monitored & conducted the vigilance test? (First)'])}',
                            '{self.handle_quotes(row['Who monitored & conducted the vigilance test? (Last)'])}',
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
                    pass
                    logging.warning(f"VAT (ID: {row['Unique ID']}) already in table 'vats'")
                else:
                    pass
                    logging.log(msg=f"VAT (ID: {row['Unique ID']}) inserted into table 'vats'", level=logging.INFO)

    def select_last_chem(self, pools: List[str]=None):
        cursor = self.connection.cursor()
        if not pools:
            pools = ['Indoor Pool']
        try:
            cursor.execute(f"""
                SELECT discord_users.id, discord_users.nickname, chem.chem_uuid, MAX(chem.sample_time) FROM
                (SELECT * FROM chem_checks WHERE pool IN ({','.join(str(pool) for pool in pools)}) AS chem
                INNER JOIN discord_users
                ON chem.discord_id = discord_users.id;
            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchone()

# if __name__ == "__main__":
#     run()
#a = YMCADatabase()
# print(a.select_discord_users([731933785, 568705929, 757270967, 564685546]))
#a = YMCADatabase()
# a.load_chems()
# formstack_time = '2020-06-10 07:05:47'
# print(datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S'))
