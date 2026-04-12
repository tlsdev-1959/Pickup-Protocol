from dataclasses import dataclass
from datetime import datetime
from objects import user

@dataclass(frozen=True)
class Session:
    session_id: str
    refresh: str
    exp: datetime

    def __init__(self: Session, user_id: int, access: str, refresh: str, exp: datetime):
        self.session_id = str(user_id) + access
        self.refresh = refresh
        self.exp = exp