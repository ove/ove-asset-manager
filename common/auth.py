from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import CollectionInvalid

VALIDATION = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["name", "year", "major", "address"],
    "properties": {
        "user": {
            "bsonType": "string",
            "description": "must be a string and is required"
        },
        "am": {
            "bsonType": "object",
            "required": ["city"],
            "properties": {

            }
        }
    }
}}


class AuthManager:
    def __init__(self, mongo_url: str, db_name: str, collection_name: str = "auth"):
        self.client = MongoClient(mongo_url)
        self.auth_collection = self.setup(db_name=db_name, collection_name=collection_name)

    def setup(self, db_name: str, collection_name: str) -> Collection:
        db = self.client[db_name]
        try:
            collection = db.create_collection(collection_name, validation={})
            collection.create_index(["user"])
            return collection
        except CollectionInvalid:
            return db[collection_name]
