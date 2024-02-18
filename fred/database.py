from __future__ import annotations

import sqlite3
import logging
import datetime
import csv
from typing import TYPE_CHECKING, List, Union
from .chem import ChemCheck
from .vat import VAT
from .oc import OpeningChecklist, ClosingChecklist
import fred.rss as rss
import fred.database_helper as dbh
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
        # self.load_chems(branch)
        # self.load_vats(branch)

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
        for user in branch.guild.members:
            self.insert_discord_user(branch, user)

    def init_w2w_users(self, branch: Branch) -> None:
        for employee in branch.w2w_client.employees:
            self.insert_w2w_employee(branch, employee)

    def insert_discord_user(self, branch: Branch, user: discord.Member):
        cursor = self.connection.cursor()
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

    def insert_w2w_employee(self, branch: Branch, employee: whentowork.Employee):
        cursor = self.connection.cursor()
        discord_id = dbh.match_discord_id(branch, employee.first_name, employee.last_name)
        discord_id = discord_id if discord_id else 'NULL'
        email = employee.emails[0] if employee.emails else ''
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









    def insert_chem(self, branch: Branch, chem: ChemCheck) -> bool:
        cursor = self.connection.cursor()
        chem_di = chem.discord_id if chem.discord_id else 'NULL'
        try:
            cursor.executescript(f"""
                BEGIN;
                INSERT INTO chem_checks
                VALUES(
                    {chem.chem_uuid}, {chem_di}, '{chem.name}', '{branch.branch_id}',
                    '{chem.pool_id}', '{chem.sample_location}', '{chem.sample_time}',
                    '{chem.submit_time}', {chem.chlorine}, {chem.ph}, {chem.water_temp},
                    {chem.num_of_swimmers}
                );
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            log.log(logging.WARN, f"Chem Check (ID: {chem.chem_uuid}) already in table 'chem_checks'")
        except Exception as e:
            log.log(logging.ERROR, f"Issue inserting Chem Check (ID: {chem.chem_uuid}). Error: {e}")
        else:
            log.log(logging.INFO, f"Chem Check (ID: {chem.chem_uuid}) inserted into table 'chem_checks'")
            return True
        return False

    def insert_vat(self, branch: Branch, vat: VAT) -> bool:
        cursor = self.connection.cursor()
        vat_gdi = vat.guard_discord_id if vat.guard_discord_id else 'NULL'
        vat_sdi = vat.sup_discord_id if vat.sup_discord_id else 'NULL'
        try:
            cursor.executescript(f"""
                BEGIN;
                INSERT INTO vats
                VALUES(
                    {vat.vat_uuid}, {vat_gdi}, '{vat.guard_name}', {vat_sdi}, '{vat.sup_name}', '{branch.branch_id}',
                    '{vat.pool_id}', '{vat.vat_time}', '{vat.submit_time}', {vat.num_of_swimmers}, {vat.num_of_guards},
                    '{vat.stimuli}', {vat.depth}, {vat.response_time}
                );
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            log.log(logging.WARN, f"VAT (ID: {vat.vat_uuid}) already in table 'vats'")
        except Exception as e:
            log.log(logging.ERROR, f"Issue inserting VAT (ID: {vat.vat_uuid}). Error: {e}")
        else:
            log.log(logging.INFO, f"VAT (ID: {vat.vat_uuid}) inserted into table 'vats'")
            return True
        return False
    
    
    def insert_opening_checklist(self, branch: Branch, o: OpeningChecklist) -> bool:
        cursor = self.connection.cursor()
        oc_di = o.discord_id if o.discord_id else 'NULL'
        try:
            cursor.executescript(f"""
                BEGIN;
                INSERT INTO opening_checklists
                VALUES(
                    {o.oc_uuid}, {oc_di}, '{o.name}', '{branch.branch_id}', '{o.checklist_group}',
                    '{o.opening_time}', '{o.submit_time}', '{o.regulatory_info}', '{o.aed_info}',
                    '{o.adult_pads_expiration_date}', '{o.pediatric_pads_expiration_date}',
                    '{o.aspirin_expiration_date}', '{o.sup_oxygen_info}', '{o.sup_oxygen_psi}', '{o.first_aid_info}',
                    {o.chlorine}, {o.ph}, {o.water_temp}, '{o.lights_function}', '{o.handicap_chair_function}',
                    '{o.spare_battery_present}', '{o.vacuum_present}'
                );
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            log.log(logging.WARN, f"Opening Checklist (ID: {o.oc_uuid}) already in table 'opening_checklists'")
        except Exception as e:
            log.log(logging.ERROR, f"Issue inserting Opening Checklist (ID: {o.oc_uuid}). Error: {e}")
        else:
            log.log(logging.INFO, f"Opening Checklist (ID: {o.oc_uuid}) inserted into table 'opening_checklists'")
            return True
        return False
    
    def insert_closing_checklist(self, branch: Branch, c: ClosingChecklist) -> bool:
        cursor = self.connection.cursor()
        oc_di = c.discord_id if c.discord_id else 'NULL'
        try:
            cursor.executescript(f"""
                BEGIN;
                INSERT INTO closing_checklists
                VALUES(
                    {c.oc_uuid}, {oc_di}, '{c.name}', '{branch.branch_id}', '{c.checklist_group}',
                    '{c.closing_time}', '{c.submit_time}', '{c.regulatory_info}', {c.chlorine}, {c.ph},
                    {c.water_temp}, '{c.lights_function}', '{c.vacuum_function}'
                );
                COMMIT;
            """)
        except sqlite3.IntegrityError:
            log.log(logging.WARN, f"Closing Checklist (ID: {c.oc_uuid}) already in table 'closing_checklists'")
        except Exception as e:
            log.log(logging.ERROR, f"Issue inserting Closing Checklist (ID: {c.oc_uuid}). Error: {e}")
        else:
            log.log(logging.INFO, f"Closing Checklist (ID: {c.oc_uuid}) inserted into table 'closing_checklists'")
            return True
        return False
    
    def load_chems(self, branch: Branch) -> None:
        with open('fred/data/chems.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                chem = ChemCheck.from_csv_row(branch, row)
                if self.insert_chem(branch, chem):
                    branch.last_chem_id = chem.chem_uuid
    
    def load_vats(self, branch: Branch) -> None:
        with open('fred/data/vats.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                vat = VAT.from_csv_row(branch, row)
                if self.insert_vat(branch, vat):
                    branch.last_chem_id = vat.vat_uuid

    def update_rss(self, branch: Branch):
        self.update_chems_rss(branch)
        self.update_vats_rss(branch)
        self.update_opening_rss(branch)
        self.update_closing_rss(branch)

    def update_chems_rss(self, branch: Branch):
        chems_rss = rss.form_rss_to_dict(branch.rss_links['chems'])
        for entry in chems_rss:
            if entry['Unique ID'] > branch.last_chem_id:
                chem = ChemCheck.from_rss_entry(branch, entry)
                if self.insert_chem(branch, chem):
                    branch.last_chem_id = chem.chem_uuid
    
    def update_vats_rss(self, branch: Branch):
        vats_rss = rss.form_rss_to_dict(branch.rss_links['vats'])
        for entry in vats_rss:
            if entry['Unique ID'] > branch.last_vat_id:
                vat = VAT.from_rss_entry(branch, entry)
                if self.insert_vat(branch, vat):
                    branch.last_vat_id = vat.vat_uuid
             
    
    def update_opening_rss(self, branch: Branch):
        opening_rss = rss.form_rss_to_dict(branch.rss_links['oc'])
        opening_rss: List[dict] = list(filter(lambda entry: entry['What checklist do you need to submit?'] == 'Opening Checklist', opening_rss))
        for entry in opening_rss:
            if entry['Unique ID'] > branch.last_opening_id:
                opening_checklist = OpeningChecklist.from_rss_entry(branch, entry)
                if self.insert_opening_checklist(branch, opening_checklist):
                    branch.last_opening_id = opening_checklist.oc_uuid
    
    def update_closing_rss(self, branch: Branch):
        closing_rss = rss.form_rss_to_dict(branch.rss_links['oc'])
        closing_rss: List[dict] = list(filter(lambda entry: entry['What checklist do you need to submit?'] == 'Closing Checklist', closing_rss))
        for entry in closing_rss:
            if entry['Unique ID'] > branch.last_closing_id:
                closing_checklist = ClosingChecklist.from_rss_entry(branch, entry)
                if self.insert_closing_checklist(branch, closing_checklist):
                    branch.last_closing_id = closing_checklist.oc_uuid






    def select_discord_user(self, branch: Branch, employee: whentowork.Employee) -> Union[discord.Member, None]:
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
                return discord_user if discord_user else None
            else:
                self.insert_w2w_employee(branch, employee)
                return self.select_discord_user(branch, employee)
            
    def select_discord_users2(self, branch: Branch, employees: List[whentowork.Employee]) -> List[discord.Member]:
        return [self.select_discord_user(branch, employee) for employee in employees if self.select_discord_user(branch, employee)]
            
    def select_discord_users(self, branch: Branch, employees: List[whentowork.Employee]) -> List[discord.Member]:
        selected_users = []
        for employee in employees:
            discord_user = self.select_discord_user(branch, employee)
            if discord_user:
                selected_users.append(discord_user)
        return selected_users

    def select_last_chem(self, branch: Branch, pool: Pool) -> ChemCheck:
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT *, MAX(sample_time) FROM chem_checks
                WHERE pool_id = '{pool.pool_id}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return ChemCheck.from_database(cursor.fetchone())

    def select_last_chems(self, branch: Branch, pools: List[Pool]) -> List[ChemCheck]:
        return [self.select_last_chem(branch, pool) for pool in pools]
    
    def select_last_opening(self, branch: Branch, checklist: str):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT *, MAX(submit_time)
                FROM opening_checklists
                WHERE checklist_group = '{checklist}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return OpeningChecklist.from_database(cursor.fetchone())

    def select_last_vat(self, branch: Branch) -> VAT:
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT *, MAX(vat_time)
                FROM vats
                WHERE branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return VAT.from_database(cursor.fetchone())
        
    def select_vats_to_date(self, branch: Branch, dt_vats_after: datetime.datetime) -> List[VAT]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT * FROM vats
                WHERE vat_time > '{dt_vats_after}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return [VAT.from_database(vat) for vat in cursor.fetchall()]
        
    def select_vats_dtd(self, branch: Branch, dt_now: datetime.datetime) -> List[VAT]:
        return self.select_vats_to_date(branch, datetime.datetime(dt_now.year, dt_now.month, dt_now.day))
        
    def select_vats_mtd(self, branch: Branch, dt_now: datetime.datetime) -> List[VAT]:
        return self.select_vats_to_date(branch, datetime.datetime(dt_now.year, dt_now.month, 1))
    
    def select_vats_ytd(self, branch: Branch, dt_now: datetime.datetime) -> List[VAT]:
        return self.select_vats_to_date(branch, datetime.datetime(dt_now.year, 1, 1))
        
    def select_chems_to_date(self, branch: Branch, dt_chems_after: datetime.datetime) -> List[ChemCheck]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"""
                SELECT * FROM chem_checks
                WHERE sample_time > '{dt_chems_after}' AND branch_id = '{branch.branch_id}';
            """)
        except Exception as e:
            print(e)
        else:
            return [ChemCheck.from_database(chem) for chem in cursor.fetchall()]
        
    def select_chems_dtd(self, branch: Branch, dt_now: datetime.datetime) -> List[ChemCheck]:
        return self.select_chems_to_date(branch, datetime.datetime(dt_now.year, dt_now.month, dt_now.day))
        
    def select_chems_mtd(self, branch: Branch, dt_now: datetime.datetime) -> List[ChemCheck]:
        return self.select_chems_to_date(branch, datetime.datetime(dt_now.year, dt_now.month, 1))
    
    def select_chems_ytd(self, branch: Branch, dt_now: datetime.datetime) -> List[ChemCheck]:
        return self.select_chems_to_date(branch, datetime.datetime(dt_now.year, 1, 1))