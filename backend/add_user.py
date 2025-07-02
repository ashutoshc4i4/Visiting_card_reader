import getpass
from pymongo import MongoClient
from flask_bcrypt import Bcrypt

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'visiting_card'
USERS_COLLECTION = 'users'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[USERS_COLLECTION]
bcrypt = Bcrypt()

def main():
    pass  # Demo user creation removed

if __name__ == '__main__':
    main() 