# models/user.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserDict:
    username: str
    email: str
    is_2fa_enabled: Optional[bool] = False

    @classmethod
    def from_db_row(cls, row: dict):
        return cls(
            username=row["username"],
            email=row["email"],
            is_2fa_enabled=row.get("is_2fa_enabled", False)
        )
