from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from ..database import Database, OrganizationDB, UserDB
from ..models import OrganizationCreate, OrganizationInDB, OrganizationUpdate, UserCreate, Token
from ..auth import AuthHandler, get_current_admin
from datetime import datetime
import logging

router = APIRouter()
auth_handler = AuthHandler()

@router.post("/create", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
async def create_organization(org_data: OrganizationCreate):
    org_db = OrganizationDB()
    user_db = UserDB()
    
    # Check if organization already exists
    existing_org = await org_db.get_organization(org_data.name)
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )
    
    # Check if email is already registered
    existing_user = await user_db.get_user_by_email(org_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Start a session for transaction
    async with await Database.client.start_session() as session:
        async with session.start_transaction():
            # Create organization
            org_data_dict = org_data.model_dump()
            org_data_dict["collection_name"] = f"org_{org_data.name.lower()}"
            org_data_dict["created_at"] = org_data_dict["updated_at"] = datetime.utcnow()
            
            # Create organization in master DB
            org = await org_db.collection.insert_one(org_data_dict, session=session)
            org_data_dict["id"] = str(org.inserted_id)
            
            # Create admin user
            hashed_password = auth_handler.get_password_hash(org_data.password)
            user_data = {
                "email": org_data.email,
                "hashed_password": hashed_password,
                "is_admin": True,
                "organization_id": str(org.inserted_id),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await user_db.collection.insert_one(user_data, session=session)
            
            # Create organization-specific collections
            org_db_instance = Database.get_org_db(org_data.name)
            # Initialize any organization-specific collections here
            await org_db_instance.create_collection("users")
            await org_db_instance.create_collection("resources")  # Example collection
            
            return OrganizationInDB(**org_data_dict)

@router.get("/get/{organization_name}", response_model=OrganizationInDB)
async def get_organization(organization_name: str, current_user: dict = Depends(auth_handler.get_current_user)):
    org_db = OrganizationDB()
    org = await org_db.get_organization(organization_name)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Only allow access to users from the same organization
    if str(org["_id"]) != current_user.get("organization_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization"
        )
    
    org["id"] = str(org["_id"])
    return OrganizationInDB(**org)

@router.put("/update/{organization_name}", response_model=OrganizationInDB)
async def update_organization(
    organization_name: str,
    org_update: OrganizationUpdate,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    org_db = OrganizationDB()
    
    # Get the organization
    org = await org_db.get_organization(organization_name)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify the admin is from the same organization
    if str(org["_id"]) != current_user.get("organization_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this organization"
        )
    
    update_data = org_update.model_dump(exclude_unset=True)
    
    # If updating the organization name, check if new name is available
    if "name" in update_data and update_data["name"] != organization_name:
        existing_org = await org_db.get_organization(update_data["name"])
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists"
            )
        
        # Update collection name
        update_data["collection_name"] = f"org_{update_data['name'].lower()}"
        
        # In a real application, you would need to handle the collection renaming here
        # This is a simplified example
        logging.warning("Organization renaming would require collection renaming logic")
    
    # Update password if provided
    if "password" in update_data:
        hashed_password = auth_handler.get_password_hash(update_data.pop("password"))
        # Update the admin user's password
        user_db = UserDB()
        await user_db.collection.update_one(
            {"email": org["email"]},
            {"$set": {"hashed_password": hashed_password}}
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update organization
    updated_org = await org_db.update_organization(organization_name, update_data)
    updated_org["id"] = str(updated_org["_id"])
    
    return OrganizationInDB(**updated_org)

@router.delete("/delete/{organization_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_name: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    org_db = OrganizationDB()
    
    # Get the organization
    org = await org_db.get_organization(organization_name)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Verify the admin is from the same organization
    if str(org["_id"]) != current_user.get("organization_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this organization"
        )
    
    # Start a session for transaction
    async with await Database.client.start_session() as session:
        async with session.start_transaction():
            # Delete organization users
            user_db = UserDB()
            await user_db.collection.delete_many(
                {"organization_id": str(org["_id"])},
                session=session
            )
            
            # Drop organization collections
            org_db_instance = Database.get_org_db(organization_name)
            await org_db_instance.drop_collection("users")
            await org_db_instance.drop_collection("resources")
            
            # Delete the organization
            await org_db.delete_organization(organization_name)
            
            # Drop the database
            await Database.client.drop_database(f"org_{organization_name.lower()}", session=session)
    
    return {"message": "Organization deleted successfully"}
