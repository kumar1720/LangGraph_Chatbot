# app/services/user.py
from typing import Optional, Union, Any

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.logger import setup_logger
from app.db.mongodb import db as mongodb

logger = setup_logger(__name__)


class UserService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db: Any = None):
        if self._initialized:
            return
        self._initialized = True

    async def get_next_id(self) -> int:
        """Generate auto-incrementing integer ID using a counters collection in MongoDB"""
        counter = await mongodb.db["counters"].find_one_and_update(
            {"_id": "user_id"},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=True
        )
        return counter["sequence_value"]

    async def get(self, user_id: int) -> Optional[User]:
        """Fetch user by auto-incremented integer ID"""
        data = await mongodb.db["users"].find_one({"id": user_id})
        return User.from_dict(data)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Fetch user by unique username"""
        data = await mongodb.db["users"].find_one({"username": username})
        return User.from_dict(data)
    
    async def create(self, obj_in: UserCreate) -> User:
        """Create a new user document in MongoDB"""
        user_data = obj_in.model_dump() if isinstance(obj_in, UserCreate) else obj_in
        
        # Generate auto-incrementing integer ID
        next_id = await self.get_next_id()
        
        password_hash = get_password_hash(user_data["password"])
        
        user_doc = {
            "id": next_id,
            "username": user_data["username"],
            "password": password_hash,
            "tenant_id": user_data["tenant_id"]
        }
        
        await mongodb.db["users"].insert_one(user_doc)
        return User.from_dict(user_doc)
    
    async def update(
        self, *, db_obj: User, obj_in: Union[UserUpdate, dict]
    ) -> User:
        """Update an existing user document in MongoDB"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if update_data.get("password"):
            password = get_password_hash(update_data["password"])
            update_data["password"] = password
        
        await mongodb.db["users"].update_one(
            {"id": db_obj.id},
            {"$set": update_data}
        )
        
        updated_doc = await mongodb.db["users"].find_one({"id": db_obj.id})
        return User.from_dict(updated_doc)
    
    async def authenticate(
        self, *, username: str, password: str
    ) -> Optional[User]:
        """Authenticate a user using their username and password"""
        user = await self.get_by_username(username=username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
