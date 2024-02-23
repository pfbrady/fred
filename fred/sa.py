from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Optional, Dict
import fred.database_helper as dbh
import datetime

if TYPE_CHECKING:
    from .branch import Branch

from enum import Enum

class Evaluation(Enum):
    EXCEED = 3
    MEET = 2
    FAIL = 1
    NA = 3

@dataclass
class ScanningAudit():
    sa_uuid: int
    guard_discord_id: Optional[int] = None
    guard_name: str = ''
    sup_discord_id: Optional[int] = None
    sup_name: str = ''
    branch_id: str = ''
    pool_id: str = ''
    time: Optional[datetime.datetime] = None
    submit_time: Optional[datetime.datetime] = None
    num_of_swimmers: int = 0
    num_of_guards: int = 0
    ten_twenty: Evaluation = Evaluation.NA
    env_concerns: Evaluation = Evaluation.NA
    professional: Evaluation = Evaluation.NA
    rescue_ready: Evaluation = Evaluation.NA
    change_of_posture: Evaluation = Evaluation.NA
    location_visual_surveillance: Evaluation = Evaluation.NA
    location_rescue_equipment: Evaluation = Evaluation.NA
    proactive_bottom_scan: Evaluation = Evaluation.NA
    without_loss_of_eye_contact: Evaluation = Evaluation.NA
    thanked: bool = False
    overall_eval: Evaluation = Evaluation.NA
    comments: Optional[str] = None
    replaced_from_stand: Optional[bool] = None
    remediation: Optional[bool] = None