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
            except Exception as error:
                logging.warning(f"Error: Connection to database 'ymca_aquatics.db' not established {error}")
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
    
    def handle_formstack_time(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S')
    
    def handle_formstack_datetime(self, formstack_time: str):
        return datetime.datetime.strptime(formstack_time, '%b %d, %Y %H:%M %p')
    
    def load_chems(self) -> None:
        print("load chems")
        cursor = self.connection.cursor()
        with open('chems_nov_2023.csv', newline='') as csvfile:
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
                            '{row['Your Name (First)']}',
                            '{row['Your Name (Last)']}',
                            '{row['Western']}',
                            '{row['Location of Water Sample, Western']}',
                            '{self.handle_formstack_datetime(row['Date/Time'])}',
                            '{self.handle_formstack_time(row['Time'])}',
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

    def select_last_chem(self, pool=None):
        cursor = self.connection.cursor()
        if not pool:
            pool = 'Indoor Pool'
        try:
            cursor.execute(f"""
                SELECT chem_uuid, first_name, last_name, MAX(sample_time) FROM
                (SELECT * FROM chem_checks WHERE pool = '{pool}')

            """)
        except Exception as e:
            print(e)
        else:
            return cursor.fetchone()


# def run():
#     con = sqlite3.connect("ymca_aquatics.db")
#     cur = con.cursor()
#     cur.executescript("""
#         BEGIN;
#         CREATE TABLE IF NOT EXISTS discord_user(id PRIMARY KEY, username, nickname, w2w_id, pectora_id);
#         CREATE TABLE IF NOT EXISTS w2w_user(id PRIMARY KEY, first_name, last_name, email, cert_expiration_date);
#         COMMIT;
#     """)

#     req = requests.get(f"https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key={settings.W2W_TOKEN}")
#     req_json = req.json()


#     for employee in req_json['EmployeeList']:
#         try:
#             cur.executescript(f"""
#                 BEGIN;
#                 INSERT INTO w2w_user
#                 VALUES({employee['W2W_EMPLOYEE_ID']}, '{employee['FIRST_NAME']}', '{employee['LAST_NAME']}', '{YMCADatabase.handle_emails(employee['EMAILS'])}', '{employee['CUSTOM_2']}');
#                 COMMIT;
#             """)
#         except sqlite3.IntegrityError:
#             logging.warning(f"Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (id: already in table 'w2w_users'")
#     con.close()

# if __name__ == "__main__":
#     run()
# a = YMCADatabase()
# print(a.select_discord_users([731933785, 568705929, 757270967, 564685546]))
# a = YMCADatabase()
# a.load_chems()
# formstack_time = '2020-06-10 07:05:47'
# print(datetime.datetime.strptime(formstack_time, '%Y-%m-%d %H:%M:%S'))