"""sa.py module"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


class Evaluation(Enum):
    """
    Enum subclass that associates each "grade" for a Scanning Audit criteria;
    for use in compliance calculations.
    """
    EXCEED = 3
    MEET = 2
    FAIL = 1
    NA = 3


@dataclass
class ScanningAudit:
    """A representation of a Formstack Scanning Audit Submission."""
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
