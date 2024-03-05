from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, TypedDict

class YMCAW2WClientPayload(TypedDict):
    director: int
    specialist: int
    supervisor: int
    swim_instructor: int
    private_swim_instructor: int
    swam: int
    lifeguards: List[int]