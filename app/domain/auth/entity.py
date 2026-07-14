from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    username: str
    password_hash: str
    id: Optional[int] = None


@dataclass
class UserSession:
    token: str
    user_id: int
    expires_at: datetime
