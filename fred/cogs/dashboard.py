from __future__ import annotations

from dataclasses import dataclass
import discord
import datetime
import fred.cogs.cog_helper as ch
from enum import Enum
from fred import ChemCheck, VAT

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Branch, ScanningAudit, InService, YMCADatabase
    from typing import List, Dict, Union, Optional
    from whentowork import Shift

class PositionType(Enum):
    SUP = 'supervisor',
    GUARD = 'lifeguard',
    INS = 'instructor'

class LengthOfTime(Enum):
    DTD = 0,
    DAY = 1,
    MTD = 15,
    MONTH = 30,
    YTD = 175,
    YEAR = 365



@dataclass
class SupervisorReportStats:
    discord_id: Optional[int] = None
    name: str = 'Supervisor w/o Discord'
    shifts: List[Shift] = []
    vats: List[VAT] = []
    chems: List[ChemCheck] = []
    scanning_audits: List[ScanningAudit] = []
    in_services: List[InService] = []

    def __post_init__(self):
        if not isinstance(self.discord_id, int):
            raise TypeError(f"Expected type of attribute discord_id is int, got {type(self.discord_id)}.")
        if not isinstance(self.name, str):
            raise TypeError(f"Expected type of attribute name is str, got {type(self.name)}.")
        if not isinstance(self.shifts, list):
            raise TypeError(f"Expected type of attribute shifts is list, got {type(self.shifts)}.")
        if not isinstance(self.vats, list):
            raise TypeError(f"Expected type of attribute vats is list, got {type(self.vats)}.")
        if not isinstance(self.chems, list):
            raise TypeError(f"Expected type of attribute chems is list, got {type(self.chems)}.")
        if not isinstance(self.scanning_audits, list):
            raise TypeError(f"Expected type of attribute scanning_audits is list, got {type(self.scanning_audits)}.")
        if not isinstance(self.in_services, list):
            raise TypeError(f"Expected type of attribute in_services is list, got {type(self.in_services)}.")

    @property
    def num_of_shifts(self):
        return len(self.shifts)
    
    @property
    def total_sup_hours(self):
        return sum(shift.duration for shift in self.shifts)
    
    @property
    def num_unique_shifts_with_vat(self):
        num_shifts = 0
        for shift in self.shifts:
            # Generator that loops over all of the vats and increments num_shifts if any of the vats happened 
            # during the current shift.
            if any(vat.vat_time >= shift.start_datetime and vat.vat_time <= shift.end_datetime for vat in self.vats):
                num_shifts += 1
        return num_shifts
    
    @property
    def num_unique_shifts_with_scanning_audit(self):
        # TODO
        return 0
    
    @property
    def num_unique_shifts_with_in_service(self):
        # TODO
        return 0

    @property
    def num_of_vats(self):
        return len(self.vats)
    
    @property
    def vats_per_shift(self):
        return self.num_of_vats() / self.num_of_shifts()
    
    @property
    def num_of_chems(self):
        return len(self.chems)
    
    @property
    def num_of_scanning_audits(self):
        return len(self.scanning_audits)
    
    @property
    def num_of_in_services(self):
        return len(self.in_services)

class Report():
    def __init__(self, position_type: PositionType, length_of_time: LengthOfTime, report_dt: datetime.datetime, **kwargs):
        self.position_type = position_type
        self.length_of_time = length_of_time
        self.report_dt = report_dt
        super().__init__(**kwargs)

class SupervisorReport(Report):
    def __init__(self, length_of_time: LengthOfTime, report_dt: datetime.datetime, **kwargs):
        self.supervisors: List[SupervisorReportStats] = []
        super().__init__(position_type=PositionType.SUP, length_of_time=length_of_time, report_dt=report_dt, **kwargs)

    def run_report(self, branch: Branch, include_vats: bool = True, include_chems: bool = True, 
            include_scan_aud: bool = True, include_in_serv: bool = True):
        discord_users = branch.guild.members if branch.guild else []
        for discord_user in discord_users:
            if branch.guild.get_role(branch.guild_role_ids['supervisor']) in discord_user.roles:
                self.supervisors.append(SupervisorReportStats(discord_user.id, discord_user.display_name))

        if include_vats:
            self.vat_report(branch)
        if include_chems:
            self.chem_report(branch)
        if include_scan_aud:
            pass
            #TODO
        if include_in_serv:
            pass
            #TODO
        
        shift_dict_by_sup = branch.w2w_client.shifts_sorted_by_employee_id(datetime.date(self.report_dt.year, self.report_dt.month, 1), self.report_dt.date(), [branch.w2w_client.supervisor])
        for w2w_employee_id, shift_list in shift_dict_by_sup.items():
            discord_user = database.select_discord_user(self.branch, self.branch.get_w2w_employee_by_id(w2w_employee_id)) if self.branch.guild else None
            if discord_user and discord_user.id in self.vbs_complete:

    def vat_report(self, branch: Branch):
        database = branch.ymca.database
        if self.length_of_time == LengthOfTime.DTD:
            vats = database.select_vats_dtd(branch, self.report_dt)
        if self.length_of_time == LengthOfTime.MTD:
            vats = database.select_vats_mtd(branch, self.report_dt)
        else:
            vats = database.select_vats_ytd(branch, self.report_dt)
        # Adding VATs to each sup
        for vat in vats:
            for sup in self.supervisors:
                if vat.sup_discord_id == sup.discord_id:
                    sup.vats.append(vat)

    def chem_report(self, branch: Branch):
        database = branch.ymca.database
        if self.length_of_time == LengthOfTime.DTD:
            chems = database.select_chems_dtd(branch, self.report_dt)
        if self.length_of_time == LengthOfTime.MTD:
            chems = database.select_chems_mtd(branch, self.report_dt)
        else:
            chems = database.select_chems_ytd(branch, self.report_dt)
        # Adding chems to each sup
        for chem in chems:
            for sup in self.supervisors:
                if chem.sup_discord_id == sup.discord_id:
                    sup.chems.append(chem)


        



class GuardReport(Report):
    def __init__(self, length_of_time: LengthOfTime, report_dt: datetime.datetime, **kwargs):
        super().__init__(position_type=PositionType.GUARD, length_of_time=length_of_time, report_dt=report_dt, **kwargs)

    # TODO

class InstructorReport(Report):
    def __init__(self, length_of_time: LengthOfTime, report_dt: datetime.datetime, **kwargs):
        super().__init__(position_type=PositionType.INS, length_of_time=length_of_time, report_dt=report_dt, **kwargs)

    # TODO


class Dashboard():
    def __init__(self, title: str, branch: Branch, color: discord.Colour = discord.Colour.from_str('#008080'), **kwargs):
        self.title = title
        self.branch = branch
        self.color = color
        super().__init__(**kwargs)

class VATSupervisorDashboard(Dashboard, Report):
    def __init__(self, branch: Branch, report_dt: datetime.datetime):
        super().__init__(title=f"Summary of VATs (Supervisors, {report_dt.strftime('%B %Y')})", branch=branch, report_type=VAT, position_type=PositionType.SUP, report_dt=report_dt)
        # title=f"Summary of VATs (Supervisors, {report_dt.strftime('%B %Y')})", branch=branch, report_type=VAT, report_dt=report_dt
        self.vbs_complete: Dict[int, list] = {}
        self.vbs_incomplete: Dict[int, list] = {}
        self.vats: List[VAT] = []
        self._populate_dashboard()

    def _populate_dashboard(self):
        database = self.branch.ymca.database

        discord_users = self.branch.guild.members if self.branch.guild else []
        for discord_user in discord_users:
            if self.branch.guild.get_role(self.branch.guild_role_ids['supervisor']) in discord_user.roles:
                # number of vats, number of shifts, ratio of vats per shift
                self.vbs_complete[discord_user.id] = [0, 0, 'N/A']

        # Adding the number of VATs to each sup total
        self.vats = database.select_vats_mtd(self.branch, self.report_dt)
        for vat in self.vats:
            if vat.sup_discord_id in self.vbs_complete:
                self.vbs_complete[vat.sup_discord_id][0] += 1
                self.vbs_complete[vat.sup_discord_id][1] = float(self.vbs_complete[vat.sup_discord_id][0])


        self.vbs_incomplete = {}
        shift_dict_by_sup = self.branch.w2w_client.shifts_sorted_by_employee_id(datetime.date(self.report_dt.year, self.report_dt.month, 1), self.report_dt.date(), [self.branch.w2w_client.supervisor])
        for w2w_employee_id, shift_list in shift_dict_by_sup.items():
            discord_user = database.select_discord_user(self.branch, self.branch.get_w2w_employee_by_id(w2w_employee_id)) if self.branch.guild else None
            if discord_user and discord_user.id in self.vbs_complete:
                num_of_shifts = len(shift_list)
                num_of_vats = self.vbs_complete[discord_user.id][0]
                ratio = num_of_vats / num_of_shifts
                if ratio < 0.75:
                    self.vbs_complete.pop(discord_user.id)
                    self.vbs_incomplete[discord_user.id] = [num_of_vats, num_of_shifts, ratio]
                else:
                    self.vbs_complete[discord_user.id][1] = num_of_shifts
                    self.vbs_complete[discord_user.id][2] = ratio



        self.vbs_complete = {k: v for k, v in sorted(self.vbs_complete.items(), key=lambda item: item[1][2], reverse=True)}
        self.vbs_incomplete = {k: v for k, v in sorted(self.vbs_incomplete.items(), key=lambda item: item[1][1])}

    @property
    def sups_in_compliance(self) -> List[discord.Member]:
        return [self.branch.get_discord_member_by_id(discord_id) for discord_id in self.vbs_complete]
    
    @property
    def embed(self):
        return discord.Embed(color=self.color, title=self.title, description=ch.vat_guard_dashboard(self.branch, self.report_dt))
    
    @property
    def total_num_of_vats(self):
        return len(self.vats)