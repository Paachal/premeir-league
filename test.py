from pymongo import MongoClient
from passlib.context import CryptContext

MONGO_DETAILS = "mongodb+srv://paschal:.adgjmptwpaschal@cluster0.dx4v8.mongodb.net/premeirdb?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_DETAILS)
db = client.premeirdb

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed_password = pwd_context.hash("123456789")
# Clear existing users to avoid duplicates
db.admin_users.delete_many({"username": "paschal0623chizi@gmail.com"})
db.admin_users.insert_one({
    "username": "paschal0623chizi@gmail.com",
    "email": "paschal0623chizi@gmail.com",
    "favorite_team": "man utd",
    "hashed_password": hashed_password
})
