import sqlite3
import requests
import settings
import logging
import time

class YMCADatabase(object):

    connection = None

    def __init__(self):
        if YMCADatabase.connection is None:
            try:
                YMCADatabase.connection = sqlite3.connect("ymca_aquatics.db")
            except Exception as error:
                logging.warning(f"Error: Connection to database 'ymca_aquatics.db' not established {error}")
            else:
                logging.log("Connection to database 'ymca_aquatics.db' established")
                self.init_tables()
                self.init_users()


    def init_tables(self):
        cursor = self.connection.cursor()
        cursor.executescript("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS discord_user(id PRIMARY KEY, username, nickname, w2w_id, pectora_id);
            CREATE TABLE IF NOT EXISTS w2w_user(id PRIMARY KEY, first_name, last_name, email, cert_expiration_date);
            COMMIT;
        """)

    def init_users(self):
        cursor = self.connection.cursor()
        req = requests.get(f"https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key={settings.W2W_TOKEN}")
        req_json = req.json()
        for employee in req_json['EmployeeList']:
            try:
                cursor.executescript(f"""
                    BEGIN;
                    INSERT INTO w2w_user
                    VALUES({employee['W2W_EMPLOYEE_ID']}, '{employee['FIRST_NAME']}', '{employee['LAST_NAME']}', '{self.handle_emails(self, employee['EMAILS'])}', '{employee['CUSTOM_2']}');
                    COMMIT;
                """)
            except sqlite3.IntegrityError:
                logging.warning(f"Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (id: already in table 'w2w_users'")

    def handle_emails(self, emails: str) -> str:
        if "," not in emails:
            return emails
        else:
            return emails.split(",")[0]
        

def run():
    con = sqlite3.connect("ymca_aquatics.db")
    cur = con.cursor()
    cur.executescript("""
        BEGIN;
        CREATE TABLE IF NOT EXISTS discord_user(id PRIMARY KEY, username, nickname, w2w_id, pectora_id);
        CREATE TABLE IF NOT EXISTS w2w_user(id PRIMARY KEY, first_name, last_name, email, cert_expiration_date);
        COMMIT;
    """)

    req = requests.get(f"https://www3.whentowork.com/cgi-bin/w2wC4.dll/api/EmployeeList?key={settings.W2W_TOKEN}")
    req_json = req.json()


    for employee in req_json['EmployeeList']:
        try:
            cur.executescript(f"""
                BEGIN;
                INSERT INTO w2w_user
                VALUES({employee['W2W_EMPLOYEE_ID']}, '{employee['FIRST_NAME']}', '{employee['LAST_NAME']}', '{YMCADatabase.handle_emails(employee['EMAILS'])}', '{employee['CUSTOM_2']}');
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            logging.warning(f"Employee {employee['FIRST_NAME']} {employee['LAST_NAME']} (id: already in table 'w2w_users'")
    con.close()

if __name__ == "__main__":
    run()