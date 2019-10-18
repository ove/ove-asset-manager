import json
import logging
import sys
from typing import Dict, Union, List

import jwt
from passlib.hash import argon2
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import CollectionInvalid

from common.consts import CONFIG_MONGO, CONFIG_MONGO_HOST, CONFIG_MONGO_PORT, CONFIG_MONGO_USER, CONFIG_MONGO_PASSWORD
from common.consts import CONFIG_MONGO_AUTH_COLLECTION, CONFIG_MONGO_DB, CONFIG_MONGO_MECHANISM
from common.consts import DEFAULT_AUTH_CONFIG, CONFIG_AUTH_JWT, CONFIG_AUTH_JWT_SECRET
from common.entities import UserAccessMeta
from common.util import to_bool

VALIDATION = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["user", "password", "am"],
    "properties": {
        "user": {
            "bsonType": "string",
            "description": "username, required"
        },
        "password": {
            "bsonType": "string",
            "description": "hashed password, required"
        },
        "am": {
            "bsonType": "object",
            "required": ["read_groups", "write_groups", "admin_access"],
            "properties": {
                "read_groups": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string",
                    },
                    "description": "read access groups, required"
                },
                "write_groups": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string",
                    },
                    "description": "write access groups, required"
                },
                "admin_access": {
                    "bsonType": "bool",
                    "description": "has admin access? required"
                },
            }
        }
    }
}}


class AuthManager:
    def __init__(self, config_file: str = DEFAULT_AUTH_CONFIG):
        self.jwt_secret = None
        self._client = None
        self._auth_collection = None

        self.load(config_file=config_file)

    def load(self, config_file: str = DEFAULT_AUTH_CONFIG):
        try:
            with open(config_file, mode="r") as fin:
                config = json.load(fin)

                jwt_config = config.get(CONFIG_AUTH_JWT, {}) or {}
                self.jwt_secret = jwt_config.get(CONFIG_AUTH_JWT_SECRET, None)

                mongo_config = config.get(CONFIG_MONGO, {}) or {}
                self._client = MongoClient(host=mongo_config.get(CONFIG_MONGO_HOST),
                                           port=mongo_config.get(CONFIG_MONGO_PORT),
                                           username=mongo_config.get(CONFIG_MONGO_USER),
                                           password=mongo_config.get(CONFIG_MONGO_PASSWORD),
                                           authSource=mongo_config.get(CONFIG_MONGO_DB),
                                           authMechanism=mongo_config.get(CONFIG_MONGO_MECHANISM))
                self._auth_collection = self.setup(db_name=mongo_config.get(CONFIG_MONGO_DB),
                                                   collection_name=mongo_config.get(CONFIG_MONGO_AUTH_COLLECTION))
                logging.info("Loaded auth config...")
        except:
            logging.error("Error while trying to load auth config. Error: %s", sys.exc_info()[1])

    def edit_user(self, access: UserAccessMeta, password: str = None, hashed: bool = False, add: bool = False) -> bool:
        db = access.to_db()
        if password:
            db["password"] = password if hashed else argon2.hash(password)

        if add:
            self._auth_collection.insert_one(db)
            return True
        else:
            result = self._auth_collection.update_one({"user": access.user}, {"$set": db})
            return result.modified_count > 0

    def remove_user(self, user: str) -> bool:
        result = self._auth_collection.delete_many({"user": user})
        return result.deleted_count > 0

    def get_groups(self) -> List[str]:
        try:
            result = set()
            result.update(self._auth_collection.distinct("am.read_groups"))
            result.update(self._auth_collection.distinct("am.write_groups"))
            return list(result)
        except:
            logging.error("Get groups Error: %s", sys.exc_info()[1])
            return []

    def get_users(self) -> List[UserAccessMeta]:
        try:
            return [self._from_db(doc) for doc in self._auth_collection.find()]
        except:
            logging.error("Get Users Error: %s", sys.exc_info()[1])
            return []

    def get_user(self, user: str) -> Union[UserAccessMeta, None]:
        try:
            return self._from_db(self._auth_collection.find_one({"user": user}))
        except:
            logging.error("Get user(%s) Error: %s", user, sys.exc_info()[1])
            return None

    def auth_user(self, user: str, password: str) -> Union[UserAccessMeta, None]:
        try:
            auth = self._auth_collection.find_one({"user": user})
            return self._from_db(auth) if argon2.verify(password, auth.get("password", None)) else None
        except:
            logging.error("Auth Error: %s", sys.exc_info()[1])
            return None

    def auth_token(self, user: str, password: str) -> Union[str, None]:
        auth = self.auth_user(user=user, password=password)
        return jwt.encode(payload=auth.public_json(), key=self.jwt_secret, algorithm="HS256").decode("utf-8") if auth else None

    def decode_token(self, token: str) -> Union[UserAccessMeta, None]:
        if not token:
            return None

        try:
            payload = jwt.decode(jwt=token.encode("utf-8"), key=self.jwt_secret, verify=True)
            return self._from_public(payload)
        except:
            logging.error("Decode Error: %s", sys.exc_info()[1])
            return None

    def setup(self, db_name: str, collection_name: str) -> Collection:
        db = self._client[db_name]
        try:
            collection = db.create_collection(collection_name, validator=VALIDATION)
            collection.create_index([("user", ASCENDING)], unique=True)
            return collection
        except CollectionInvalid:
            return db[collection_name]

    def close(self):
        self._client.close()

    @staticmethod
    def _from_db(doc: Dict) -> UserAccessMeta:
        am = doc.get("am", {}) or {}
        return UserAccessMeta(user=doc.get("user", None), admin_access=to_bool(am.get("admin_access", False)),
                              read_groups=am.get("read_groups", []) or [], write_groups=am.get("write_groups", []) or [])

    @staticmethod
    def _from_public(doc: Dict) -> UserAccessMeta:
        return UserAccessMeta(user=doc.get("user", None), admin_access=to_bool(doc.get("admin_access", False)),
                              read_groups=doc.get("read_groups", []) or [], write_groups=doc.get("write_groups", []) or [])
