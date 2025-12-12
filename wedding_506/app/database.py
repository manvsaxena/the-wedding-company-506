from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_to_mongo(cls):
        cls.client = AsyncIOMotorClient(settings.mongodb_url)
        
    @classmethod
    async def close_mongo_connection(cls):
        if cls.client:
            cls.client.close()
            
    @classmethod
    def get_master_db(cls):
        return cls.client[settings.master_db_name]
        
    @classmethod
    def get_org_db(cls, org_name: str):
        """Get database instance for a specific organization"""
        return cls.client[f"org_{org_name.lower()}"]

# Database models
class OrganizationDB:
    def __init__(self):
        self.collection = Database.get_master_db().organizations
        
    async def get_organization(self, organization_name: str):
        return await self.collection.find_one({"name": organization_name})
    
    async def create_organization(self, organization_data: dict):
        result = await self.collection.insert_one(organization_data)
        return await self.collection.find_one({"_id": result.inserted_id})
    
    async def update_organization(self, organization_name: str, update_data: dict):
        await self.collection.update_one(
            {"name": organization_name},
            {"$set": update_data}
        )
        return await self.get_organization(organization_name)
    
    async def delete_organization(self, organization_name: str):
        return await self.collection.delete_one({"name": organization_name})

class UserDB:
    def __init__(self):
        self.collection = Database.get_master_db().users
        
    async def get_user_by_email(self, email: str):
        return await self.collection.find_one({"email": email})
    
    async def create_user(self, user_data: dict):
        result = await self.collection.insert_one(user_data)
        return await self.collection.find_one({"_id": result.inserted_id})
