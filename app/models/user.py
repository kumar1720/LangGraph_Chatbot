# app/models/user.py
from typing import Dict, Any, Optional

class User:
    def __init__(self, id: int, username: str, password: str, tenant_id: str):
        self.id = id
        self.username = username
        self.password = password
        self.tenant_id = tenant_id

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['User']:
        if not data:
            return None
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            password=data.get("password"),
            tenant_id=data.get("tenant_id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "tenant_id": self.tenant_id
        }
