from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client.users_database
collection = db.users_collection

# Define the User model
class User(BaseModel):
    name: str
    email: str

class UserInDB(User):
    id: str

@app.post("/users/", response_model=UserInDB)
async def create_user(user: User):
    user_dict = user.dict()
    result = await collection.insert_one(user_dict)
    user_in_db = UserInDB(id=str(result.inserted_id), **user_dict)
    return user_in_db

@app.get("/users/", response_model=List[UserInDB])
async def read_users():
    users = await collection.find().to_list(length=100)
    return [UserInDB(id=str(user["_id"]), name=user["name"], email=user["email"]) for user in users]

@app.get("/users/{user_id}", response_model=UserInDB)
async def read_user(user_id: str):
    user = await collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserInDB(id=str(user["_id"]), name=user["name"], email=user["email"])

@app.put("/users/{user_id}", response_model=UserInDB)
async def update_user(user_id: str, updated_user: User):
    result = await collection.update_one({"_id": ObjectId(user_id)}, {"$set": updated_user.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user = await collection.find_one({"_id": ObjectId(user_id)})
    return UserInDB(id=str(user["_id"]), name=user["name"], email=user["email"])

@app.delete("/users/{user_id}", response_model=UserInDB)
async def delete_user(user_id: str):
    user = await collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await collection.delete_one({"_id": ObjectId(user_id)})
    return UserInDB(id=str(user["_id"]), name=user["name"], email=user["email"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
