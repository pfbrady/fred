from __future__ import annotations

import discord
import datetime
from enum import Enum
from fred import ChemCheck, VAT

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Branch, ScanningAudit, InService
    from typing import List, Dict, Union, Optional, Tuple
    from whentowork import Shift

class PositionType(Enum):
    SUPERVISOR = 'supervisor'
    LIFEGUARD = 'lifeguard'
    INSTRUCTOR = 'instructor'

class ReportType(Enum):
    DTD = 'Day-to-Date'
    DAY = 'Day'
    MTD = 'Month-to-Date'
    MONTH = 'Month'
    YTD = 'Year-to-Date'
    YEAR = 'Year'

class ShiftReport:
    def __init__(self):
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
    
class ComplianceStrategy:
    def __init__(
            self,
            percentage_of_shifts_target: Optional[float] = None,
            items_per_shift_target: Optional[float] = None,
            items_per_hour_target: Optional[float] = None,
            num_target: Optional[int] = None):
        self.percentage_of_shifts_target = percentage_of_shifts_target
        self.items_per_shift_target = items_per_shift_target
        self.items_per_hour_target = items_per_hour_target
        self.num_target = num_target

    def calc_in_comp(
            self,
            percentage_of_shifts: Optional[float] = None,
            items_per_shift: Optional[float] = None,
            items_per_hour: Optional[float] = None,
            num: Optional[int] = None) -> bool:
        in_compliance = True
        if self.percentage_of_shifts_target and isinstance(percentage_of_shifts, float):
            in_compliance = True if percentage_of_shifts >= self.percentage_of_shifts_target else False
        if self.items_per_shift_target and isinstance(items_per_shift, float):
            in_compliance = True if items_per_shift >= self.items_per_shift_target else False
        if self.items_per_hour_target and isinstance(items_per_hour, float):
            in_compliance = True if items_per_hour >= self.items_per_hour_target else False
        if self.num_target and isinstance(num, int):
            in_compliance = True if num >= self.num_target else False
        return in_compliance

class InServComplianceStrategy(ComplianceStrategy):
    def init(
            self,
            hours_per_time_period_target: float,
            percentage_of_shifts_target: Optional[float] = None,
            items_per_shift_target: Optional[float] = None,
            items_per_hour_target: Optional[float] = None,
            num_target: Optional[int] = None):
        super().__init__(
            percentage_of_shifts_target,
            items_per_shift_target,
            items_per_hour_target,
            num_target)
        self.hours_per_time_period_target = hours_per_time_period_target
    
    def calc_in_comp(
            self,
            hours_per_time_period: Optional[float] = None,
            percentage_of_shifts: Optional[float] = None,
            items_per_shift: Optional[float] = None,
            items_per_hour: Optional[float] = None,
            num: Optional[int] = None) -> bool:
        in_compliance = super().calc_in_comp(percentage_of_shifts, items_per_shift, items_per_hour, num)
        if self.hours_per_time_period_target and isinstance(hours_per_time_period, float): 
            in_compliance = True and in_compliance if hours_per_time_period > self.hours_per_time_period_target else False
        return in_compliance


class ReportItem():
    def __init__(
            self,
            shift_report: ShiftReport,
            name: str,
            abbreviation: Optional[str] = None,
            weight: int = 0,
            compliance_strat: ComplianceStrategy = ComplianceStrategy()):
        self.shift_report = shift_report
        self.compliance_strat = compliance_strat
        self.name = name
        self.abbr = abbreviation
        self._weight = weight
        self.items: List[Union[VAT, ChemCheck, ScanningAudit, InService]] = []

    @property
    def num(self) -> int:
        return len(self.items)
    
    @property
    def weight(self) -> int:
        return self._weight if self.shift_report.num_of_shifts else 0

    @property
    def in_compliance(self) -> bool:
        return self.compliance_strat.calc_in_comp(self.shift_unique_percentage, self.per_shift, self.per_hour, self.num)
    
    @property
    def per_hour(self) -> Union[float, str]:
            return self.num / self.shift_report.total_hours if self.shift_report.total_hours else 'N/A'

    @property
    def per_shift(self) -> Union[float, str]:
        if self.shift_report.num_of_shifts:
            return self.num / self.shift_report.num_of_shifts
        elif self.num:
            return float(self.num)
        else:
            return 'N/A'
    
    @property
    def num_shifts_with_unique(self) -> int:
        if self.shift_report.num_of_shifts == 0:
            return 0
        num_shifts = 0
        for shift in self.shift_report.shifts:
            # Generator that loops over all of the items and increments num_shifts if any of the items happened 
            # during the current shift.
            if any(item.time >= shift.start_datetime and item.time <= shift.end_datetime for item in self.items if isinstance(item.time, datetime.datetime)):
                num_shifts += 1
        return num_shifts
    
    @property
    def shift_unique_percentage(self):
        return self.num_shifts_with_unique / self.shift_report.num_of_shifts if self.shift_report.num_of_shifts else 'N/A'
    
    @property
    def summary(self) -> str:
        abbr = self.abbr if self.abbr else self.name
        uni_per = self.shift_unique_percentage
        uni_per = f'{uni_per:.1%}' if isinstance(uni_per, float) else uni_per
        per_shift = self.per_shift
        if isinstance(per_shift, float):
            per_shift = "{:.2f}".format(per_shift)
        return f'{self.name}s: **{self.num}**\t {abbr}s/Shift: **{per_shift}**\t Shift {abbr} %: **{uni_per}**\n'
    
    @property
    def mobile_summary(self) -> str:
        return f'{self.name}s: **{self.num}\t**'

class ReportStats:
    def __init__(self, discord_id: int, name: str, report_type: ReportType, **kwargs):
        self.discord_id = discord_id
        self.name = name
        self.report_type = report_type
        self.shift_report = ShiftReport()
        super().__init__(**kwargs)

    @property
    def items(self) -> List[ReportItem]:
        return []

    @property
    def in_compliance(self) -> bool:
        return all([item.in_compliance for item in self.items])
    
    @property
    def total_score(self) -> int:
        return sum([item.weight for item in self.items if item.in_compliance])

    @property
    def mobile_summary(self) -> str:
        return f'**{self.name}**\nShifts: **{self.shift_report.num_of_shifts}**\t Total Hours: **{"{:.2f}".format(self.shift_report.total_hours)}**\n{"".join([item.mobile_summary for item in self.items])}\n'

    @property
    def summary(self) -> str:
        return f'<@{self.discord_id}>\nShifts: **{self.shift_report.num_of_shifts}**\t Total Hours: **{"{:.2f}".format(self.shift_report.total_hours)}**\n{"".join([item.summary for item in self.items])}'

class SupervisorReportStats(ReportStats):
    def __init__(
            self,
            discord_id: Optional[int],
            name: Optional[str],
            report_type: ReportType,
            include_vats: bool = True, 
            include_chems: bool = True,
            include_scan_auds: bool = True,
            include_in_servs: bool = True,
            **kwargs):
        super().__init__(discord_id=discord_id, name=name, report_type=report_type, **kwargs)
        self.vats = ReportItem(
            self.shift_report,
            'VAT',
            weight=5,
            compliance_strat=ComplianceStrategy(0.75, 0.75)) if include_vats else None
        self.chems = ReportItem(
            self.shift_report,
            'Chemical Check',
            'Chem',
            2,
            ComplianceStrategy(0.95, items_per_hour_target=1.0)) if include_chems else None
        self.scan_auds = ReportItem(self.shift_report, 'Scanning Audit', 'SA', 3) if include_scan_auds else None
        self.in_servs = ReportItem(self.shift_report, 'In Service', 'IS', 2) if include_in_servs else None

    @property
    def items(self) -> List[ReportItem]:
        return [item for item in [self.vats, self.chems, self.scan_auds, self.in_servs] if item]

class GuardReportStats(ReportStats):
    def __init__(
            self,
            discord_id: Optional[int],
            name: Optional[str],
            report_type: ReportType,
            include_vats: bool = True,
            include_scan_auds: bool = True,
            include_in_servs: bool = True,
            **kwargs):
        super().__init__(discord_id=discord_id, name=name, report_type=report_type, **kwargs)
        if self.report_type == ReportType.DAY or self.report_type == ReportType.DTD:
            num_target = 0
        elif self.report_type == ReportType.MONTH or self.report_type == ReportType.MTD:
            num_target = 1
        else:
            num_target = 12
        self.vats = ReportItem(
            self.shift_report,
            'VAT',
            compliance_strat=ComplianceStrategy(num_target=num_target)) if include_vats else None
        self.scan_auds = ReportItem(
            self.shift_report,
            'Scanning Audit',
            'SA',
            ComplianceStrategy(items_per_shift_target=0.50)) if include_scan_auds else None
        self.in_servs = ReportItem(
            self.shift_report,
            'In Service',
            'IS',
            ComplianceStrategy(num_target=2*num_target)) if include_in_servs else None

    @property
    def items(self) -> List[ReportItem]:
        return [item for item in [self.vats, self.scan_auds, self.in_servs] if item]
    


class Report():
    def __init__(
            self,
            users: List[ReportStats],
            position_type: PositionType,
            report_type: ReportType,
            report_dt: datetime.datetime):
        self.users = users
        self.position_type = position_type
        self.report_type = report_type
        self.report_dt = report_dt
        self.start_dt, self.end_dt = self.report_time_elapsed
        self.color = discord.Colour.from_str('#008080')
        self.title = f'{self.position_type.value.capitalize()} {self.report_type.value} Report'
        self.footer = f"{self.report_dt.strftime('%d %b %Y, %I:%M%p')}"

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
        return sum(user.shift_report.num_of_shifts for user in self.users)
    
    @property
    def total_hours(self) -> float:
        return sum(user.shift_report.total_hours for user in self.users)
    
    def num_of_items(self, item_name: str) -> int:
        return sum(item.num for emp in self.users for item in emp.items if item.name == item_name)
    
    def num_of_shifts_with_unique_item(self, item_name: str) -> int:
        return sum(item.num_shifts_with_unique for emp in self.users for item in emp.items if item.name == item_name)

    def ratio_of_shifts_with_unique_item(self, item_name: str) -> Union[float, str]:
        return self.num_of_shifts_with_unique_item(item_name) / self.total_num_of_shifts if self.total_num_of_shifts else 'N/A'
    
    def run_report(self, branch: Branch, run_by: discord.User, **kwargs) -> None:
        self.footer = f'Run by {run_by.display_name} at {self.footer}'
        if branch.guild:
            discord_users = branch.guild.members
            discord_role = branch.guild.get_role(branch.guild_role_ids[self.position_type.value])
        else:
            discord_users = []
            discord_role = None

        for discord_user in discord_users:
            if discord_role in discord_user.roles:
                self.users.append({
                    PositionType.LIFEGUARD: GuardReportStats,
                    PositionType.SUPERVISOR: SupervisorReportStats,
                    PositionType.INSTRUCTOR: ReportStats
                }[self.position_type](discord_user.id, discord_user.display_name, self.report_type, **kwargs))

        positions = {
            PositionType.LIFEGUARD: branch.w2w_client.lifeguard_positions,
            PositionType.SUPERVISOR: [branch.w2w_client.supervisor],
            PositionType.INSTRUCTOR: [branch.w2w_client.swim_instructor]
        }[self.position_type]
        shift_dict_by_emp = branch.w2w_client.shifts_sorted_by_employee(
            self.start_dt, self.end_dt, positions)
        for w2w_employee, shift_list in shift_dict_by_emp.items():
            discord_user = branch.ymca.database.select_discord_user(
                branch, branch.get_w2w_employee_by_id(w2w_employee.id)) if branch.guild else None
            if discord_user:
                for emp in self.users:
                    if emp.discord_id == discord_user.id:
                        emp.shift_report.shifts = shift_list

    async def send_report(self, channel: Optional[discord.TextChannel] = None, interaction: Optional[discord.Interaction] = None, mobile: bool = True) -> None:
        original_desc = ''.join(self.summaries_as_list(mobile=mobile))
        full_message = f"## {self.title}\n{original_desc}\n{self.footer}"
        if mobile:
            if len(full_message) <= 2000:
                if interaction:
                    await interaction.response.send_message(full_message, ephemeral=True)
                if channel:
                    await channel.send(full_message)
            else:
                chunks = self.chunk_summaries(2000, 10, mobile)
                if interaction:
                    paginator = ReportPaginator(self.title, self.footer, chunks, mobile)
                    await paginator.send(interaction)
                if channel:
                    for chunk in chunks:
                        await channel.send(chunk)
        else:
            if len(original_desc) <= 4096:
                embed = discord.Embed(color=self.color, title=self.title, description=original_desc)
                embed.set_footer(text=self.footer)
                if interaction:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                if channel:
                    await channel.send(embed=embed)
            else:
                chunks = self.chunk_summaries(4096, 10)
                if interaction:
                    paginator = ReportPaginator(self.title, self.footer, chunks, mobile)
                    await paginator.send(interaction)
                if channel:
                    for index, chunk in enumerate(chunks):
                        embed = discord.Embed(color=self.color, title=f'{self.title} (Page {index + 1})', description=chunk)
                        await channel.send(embed=chunk)




    def sort_users(self):
        # Sorts by total score (descending) then number of shifts (ascending)
        self.users.sort(key = lambda user: (user.total_score, -user.shift_report.num_of_shifts), reverse=True)

    @property
    def users_in_compliance(self) -> List[ReportStats]:
        return [user for user in self.users if user.in_compliance]
    
    @property
    def users_not_in_compliance(self) -> List[ReportStats]:
        return [user for user in self.users if not user.in_compliance]
        
    def chunk_summaries(self, max_chunk_size: int, max_chunks: int, mobile: bool = False) -> List[str]:
        chunks: List[str] = []
        cur_chunk = ''
        mcs = max_chunk_size - len(self.title) - len(self.footer) - 50 if mobile else max_chunk_size
        for summary in self.summaries_as_list(mobile):
            if len(chunks) == max_chunks:
                return chunks
            chunk_cat = cur_chunk + summary
            if len(chunk_cat) <= mcs:
                cur_chunk += summary
            else:
                chunks.append(cur_chunk)
                cur_chunk = summary
        chunks.append(cur_chunk)
        return [f"## {self.title} (Page {index + 1})\n{chunk}\n{self.footer}" for index, chunk in enumerate(chunks)] if mobile else chunks
       
    def summaries_as_list(self, mobile: bool = False) -> List[str]:
        summaries = [user.mobile_summary for user in self.users_in_compliance] if mobile else [user.summary for user in self.users_in_compliance]
        summaries.extend([] if mobile else ['**--------------------**\n'])
        summaries.extend([user.mobile_summary for user in self.users_not_in_compliance] if mobile else [user.summary for user in self.users_not_in_compliance])
        return summaries
        
class ReportPaginator(discord.ui.View):
    def __init__(self, title: str, footer: str, chunks: List[str], mobile: bool = True):
        super().__init__()
        self.title = title
        self.footer = footer
        self.chunks = chunks
        self.embeds = None if mobile else [discord.Embed(title=f'{self.title} (Page {index + 1})', description=chunk) for index, chunk in enumerate(chunks)]
        if self.embeds:
            for embed in self.embeds:
                embed.set_footer(text=footer)
        self.index: int = 0

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=self, ephemeral=True)
        await self.update_message(interaction)

    def update_buttons(self):
        self.left.disabled = False
        self.right.disabled = False
        if self.index == 0:
            self.left.disabled = True
        if self.index == len(self.chunks) - 1:
            self.right.disabled = True
    
    async def update_message(self, interaction: discord.Interaction):
        self.update_buttons()
        if self.embeds:
            await interaction.edit_original_response(embed=self.embeds[self.index], view=self)
        else:
            await interaction.edit_original_response(content=self.chunks[self.index], view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.index = max(self.index - 1, 0)
        await self.update_message(interaction) 

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.index = min(self.index + 1, len(self.chunks) - 1)
        await self.update_message(interaction)        
        
        

class SupervisorReport(Report):
    def __init__(self, report_type: ReportType, report_dt: datetime.datetime, **kwargs):
        self.supervisors: List[SupervisorReportStats] = []
        super().__init__(users=self.supervisors, position_type=PositionType.SUPERVISOR, report_type=report_type, report_dt=report_dt, **kwargs)

    def run_report(self, branch: Branch, run_by: discord.User, include_vats: bool = False, include_chems: bool = False,
            include_scan_auds: bool = False, include_in_servs: bool = False) -> None:
        super().run_report(
            branch,
            run_by,
            include_vats=include_vats,
            include_chems=include_chems,
            include_scan_auds=include_scan_auds,
            include_in_servs=include_in_servs)
        if include_vats:
            self.vat_report(branch)
        if include_chems:
            self.chem_report(branch)
        if include_scan_auds:
            pass
            #TODO
        if include_in_servs:
            pass
            #TODO
        self.sort_users()

    def vat_report(self, branch: Branch) -> None:
        database = branch.ymca.database
        vats = database.select_vats(branch, self.start_dt, self.end_dt)

        # Adding VATs to each sup
        for vat in vats:
            for sup in self.supervisors:
                if vat.sup_discord_id == sup.discord_id:
                    sup.vats.items.append(vat)

    def chem_report(self, branch: Branch) -> None:
        database = branch.ymca.database
        chems = database.select_chems(branch, self.start_dt, self.end_dt)

        # Adding chems to each sup
        for chem in chems:
            for sup in self.supervisors:
                if sup.shift_report.during_shifts(chem.time):
                    sup.chems.items.append(chem)

class GuardReport(Report):
    def __init__(self, report_type: ReportType, report_dt: datetime.datetime, **kwargs):
        self.guards: List[GuardReportStats] = []
        super().__init__(users=self.guards, position_type=PositionType.LIFEGUARD, report_type=report_type, report_dt=report_dt, **kwargs)

    def run_report(self, branch: Branch, run_by: discord.User, include_vats: bool = False, include_scan_auds: bool = False,
            include_in_servs: bool = False) -> None:
        super().run_report(
            branch,
            run_by,
            include_vats=include_vats,
            include_scan_auds=include_scan_auds,
            include_in_servs=include_in_servs)
        if include_vats:
            self.vat_report(branch)
        if include_scan_auds:
            pass
            #TODO
        if include_in_servs:
            pass
            #TODO
        self.sort_users()

    def vat_report(self, branch: Branch) -> None:
        database = branch.ymca.database
        vats = database.select_vats(branch, self.start_dt, self.end_dt)

        # Adding VATs to each sup
        for vat in vats:
            for guard in self.guards:
                if vat.guard_discord_id == guard.discord_id:
                    guard.vats.items.append(vat)
