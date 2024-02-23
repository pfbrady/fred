from __future__ import annotations

from dataclasses import dataclass
import discord
import datetime
import fred.cogs.cog_helper as ch
from enum import Enum
from fred import ChemCheck, VAT

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Branch, ScanningAudit, InService
    from typing import List, Dict, Union, Optional, Tuple
    from whentowork import Shift

class PositionType(Enum):
    SUPERVISOR = 'supervisor',
    LIFEGUARD = 'lifeguard',
    INSTRUCTOR = 'instructor'

class ReportType(Enum):
    DTD = 'Day-to-date',
    DAY = 'Day',
    MTD = 'Month-to-date',
    MONTH = 'Month',
    YTD = 'Year-to-date',
    YEAR = 'Year'

class ReportStats:
    def __init__(self, discord_id: Optional[int] = None, name: Optional[str] = None):
        self.discord_id = discord_id
        self.name = name
        self.shifts: List[Shift] = []
    
    @property
    def num_of_shifts(self) -> int:
        return len(self.shifts)
    
    @property
    def total_hours(self) -> float:
        return sum(shift.duration for shift in self.shifts)
    
    def during_shifts(self, dt: datetime.datetime) -> bool:
        for shift in self.shifts:
            if dt >= shift.start_datetime and dt <= shift.end_datetime:
                return True
        return False

    

class SupervisorReportStats(ReportStats):
    def __init__(self, discord_id: Optional[int], name: Optional[str]):
        self.vats: List[VAT] = []
        self.chems: List[ChemCheck] = []
        self.scan_auds: List[ScanningAudit] = []
        self.in_servs: List[InService] = []
        super().__init__(discord_id=discord_id, name=name)
        
    @property
    def in_compliance(self) -> bool:
        return self.in_vat_compliance and self.in_chems_compliance and self.in_scan_aud_compliance \
            and self.in_in_serv_compliance

    # VATS SUMMARY STATS

    @property
    def num_of_vats(self):
        return len(self.vats)
    
    @property
    def in_vat_compliance(self) -> bool:
        return not self.num_of_shifts or self.vats_per_shift > 0.75
    
    @property
    def vats_per_shift(self) -> Union[float, str]:
        if self.num_of_shifts:
            return self.num_of_vats / self.num_of_shifts
        elif self.num_of_vats:
            return float(self.num_of_vats)
        else:
            return 'N/A'

    @property
    def num_shifts_with_unique_vat(self) -> int:
        if self.num_of_shifts == 0:
            return 0
        num_shifts = 0
        for shift in self.shifts:
            # Generator that loops over all of the vats and increments num_shifts if any of the vats happened 
            # during the current shift.
            if any(vat.vat_time >= shift.start_datetime and vat.vat_time <= shift.end_datetime for vat in self.vats):
                num_shifts += 1
        return num_shifts
    
    @property
    def ratio_of_shifts_with_unique_vat(self) -> Union[float, str]:
        return self.num_shifts_with_unique_vat / self.num_of_shifts if self.num_of_shifts else 'N/A'
    
    # CHEM SUMMARY STATS

    @property
    def num_of_chems(self) -> int:
        return len(self.chems)
    
    @property
    def in_chems_compliance(self) -> bool:
        return not self.num_of_shifts or self.chems_per_two_hour > 1.0
    
    @property
    def chems_per_two_hour(self) -> Union[float, str]:
            return 0.5*self.total_hours / self.num_of_chems if self.num_of_shifts else 'N/A'

    # SCANNING AUDIT SUMMARY STATS

    @property
    def num_of_scan_auds(self) -> int:
        return len(self.scan_auds)

    @property
    def in_scan_aud_compliance(self) -> bool:
        # TODO
        return not self.num_of_shifts or True

    @property
    def num_shifts_with_unique_scan_aud(self):
        # TODO
        return self.num_of_shifts
    
    @property
    def ratio_of_shifts_with_unique_scan_aud(self) -> Union[float, str]:
        # TODO
        return 'N/A'
    
    # IN SERVICE SUMMARY STATS

    @property
    def num_of_in_servs(self) -> int:
        return len(self.in_servs)
    
    @property
    def in_in_serv_compliance(self):
        # TODO
        return not self.num_of_shifts or True

    @property
    def num_shifts_with_unique_in_servs(self):
        # TODO
        return self.num_of_shifts
    
    @property
    def ratio_of_shifts_with_unique_in_serv(self) -> Union[float, str]:
        # TODO
        return 'N/A'
    

class Report():
    def __init__(
            self,
            users: List[ReportStats],
            position_type: PositionType,
            report_type: ReportType,
            report_dt: datetime.datetime,
            **kwargs):
        self.users = users
        self.position_type = position_type
        self.report_type = report_type
        self.report_dt = report_dt
        self.color = discord.Colour.from_str('#008080')
        self.title = f'{self.report_type.value} report for {self.position_type.name} (Updated: {self.report_dt.isoformat()})'
        super().__init__(**kwargs)

    @property
    def report_time_elapsed(self) -> Tuple[datetime.datetime, datetime.datetime]:
        return {ReportType.DTD:
             (datetime.datetime(self.report_dt.year, self.report_dt.month, self.report_dt.day, 0, 1), self.report_dt),
         ReportType.DAY: (self.report_dt - datetime.timedelta(1), self.report_dt),
         ReportType.MTD: (datetime.datetime(self.report_dt.year, self.report_dt.month, 1, 0, 1), self.report_dt),
         ReportType.MONTH: (self.report_dt - datetime.timedelta(30), self.report_dt),
         ReportType.YTD: (datetime.datetime(self.report_dt.year, 1, 1, 0, 1), self.report_dt),
         ReportType.YEAR: (self.report_dt - datetime.timedelta(365), self.report_dt)}[self.report_type]
    
    @property
    def total_num_of_shifts(self) -> int:
        return sum(user.num_of_shifts for user in self.users)
    
    @property
    def total_hours(self) -> float:
        return sum(user.total_hours for user in self.users)
    
    def run_report(self, branch: Branch) -> None:
        if branch.guild:
            discord_users = branch.guild.members
            discord_role = branch.guild.get_role(branch.guild_role_ids[self.position_type.value])
        else:
            discord_users = []
            discord_role = None

        for discord_user in discord_users:
            if discord_role in discord_user.roles:
                self.users.append({
                    PositionType.LIFEGUARD: ReportStats,
                    PositionType.SUPERVISOR: SupervisorReportStats,
                    PositionType.INSTRUCTOR: ReportStats
                }[self.position_type](discord_user.id, discord_user.display_name))

        start_dt, end_dt = self.report_time_elapsed
        positions = {
            PositionType.LIFEGUARD: branch.w2w_client.lifeguards,
            PositionType.SUPERVISOR: [branch.w2w_client.supervisor],
            PositionType.INSTRUCTOR: [branch.w2w_client.swim_instructor]
        }[self.position_type]
        shift_dict_by_emp = branch.w2w_client.shifts_sorted_by_employee(
            start_dt.date(), end_dt.date(), positions)
        for w2w_employee, shift_list in shift_dict_by_emp.items():
            discord_user = branch.ymca.database.select_discord_user(
                branch, branch.get_w2w_employee_by_id(w2w_employee.id)) if branch.guild else None
            if discord_user:
                for emp in self.users:
                    if emp.discord_id == discord_user.id:
                        emp.shifts = shift_list

    @property
    def embed(self):
        return discord.Embed(color=self.color, title=self.title, description='DASHBOARD DESCRIPTION')
        
        
        
        

class SupervisorReport(Report):
    def __init__(self, report_type: ReportType, report_dt: datetime.datetime, **kwargs):
        self.supervisors: List[SupervisorReportStats] = []
        self.color = discord.Colour.from_str('#008080')
        super().__init__(users=self.supervisors, position_type=PositionType.SUP, report_type=report_type, report_dt=report_dt, **kwargs)

    def run_report(self, branch: Branch, include_vats: bool = True, include_chems: bool = True,
            include_scan_aud: bool = True, include_in_serv: bool = True):
        super().run_report(branch)
        start_dt, end_dt = self.report_time_elapsed
        if include_vats:
            self.vat_report(branch, start_dt, end_dt)
        if include_chems:
            self.chem_report(branch, start_dt, end_dt)
        if include_scan_aud:
            pass
            #TODO
        if include_in_serv:
            pass
            #TODO

    def vat_report(self, branch: Branch, start_dt: datetime.datetime, end_dt: datetime.datetime):
        database = branch.ymca.database
        vats = database.select_vats(branch, start_dt, end_dt)

        # Adding VATs to each sup
        for vat in vats:
            for sup in self.supervisors:
                if vat.sup_discord_id == sup.discord_id:
                    sup.vats.append(vat)

    def chem_report(self, branch: Branch, start_dt: datetime.datetime, end_dt: datetime.datetime):
        database = branch.ymca.database
        chems = database.select_chems(branch, start_dt, end_dt)

        # Adding chems to each sup
        for chem in chems:
            for sup in self.supervisors:
                if sup.during_shifts(chem.sample_time):
                    sup.chems.append(chem)

    @property
    def sups_in_compliance(self):
        return [sup for sup in self.supervisors if sup.in_compliance]
    
    @property
    def sups_not_in_compliance(self):
        return [sup for sup in self.supervisors if not sup.in_compliance]

    # VATS SUMMARY STATS
    
    @property
    def branch_num_of_vats(self) -> int:
        return sum(sup.num_of_vats for sup in self.supervisors)





class GuardReport(Report):
    def __init__(self, report_type: ReportType, report_dt: datetime.datetime, **kwargs):
        super().__init__(position_type=PositionType.GUARD, report_type=report_type, report_dt=report_dt, **kwargs)

    # TODO

class InstructorReport(Report):
    def __init__(self, report_type: ReportType, report_dt: datetime.datetime, **kwargs):
        super().__init__(position_type=PositionType.INS, report_type=report_type, report_dt=report_dt, **kwargs)

    # TODO


class Dashboard():
    def __init__(self, title: str, color: discord.Colour = discord.Colour.from_str('#008080'), **kwargs):
        self.title = title
        self.color = color
        super().__init__(**kwargs)

