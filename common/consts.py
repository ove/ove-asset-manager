DEFAULT_CREDENTIALS_CONFIG = "config/credentials.json"
DEFAULT_AUTH_CONFIG = "config/auth.json"

CONFIG_STORE_DEFAULT = "default"
CONFIG_STORES = "stores"
CONFIG_STORE_NAME = "name"
CONFIG_ENDPOINT = "endpoint"
CONFIG_ACCESS_KEY = "accessKey"
CONFIG_SECRET_KEY = "secretKey"
CONFIG_PROXY_URL = "proxyUrl"

CONFIG_AUTH_JWT = "jwt"
CONFIG_AUTH_JWT_SECRET = "secret"
CONFIG_AUTH_MONGO = "mongo"
CONFIG_AUTH_MONGO_HOST = "host"
CONFIG_AUTH_MONGO_PORT = "port"
CONFIG_AUTH_MONGO_USER = "user"
CONFIG_AUTH_MONGO_PASSWORD = "password"
CONFIG_AUTH_MONGO_DB = "db"
CONFIG_AUTH_MONGO_COLLECTION = "collection"
CONFIG_AUTH_MONGO_MECHANISM = "mechanism"

FIELD_AUTH_TOKEN = "AUTH_TOKEN"

OVE_META = ".ovemeta"
PROJECT_FILE = "project.json"

PROJECT_METADATA_SECTION = "Metadata"
PROJECT_SECTIONS = "Sections"
PROJECT_BASIC_TEMPLATE = {PROJECT_METADATA_SECTION: {}, PROJECT_SECTIONS: []}

S3_SEPARATOR = "/"

S3_OBJECT_EXTENSION = ".json"

MAX_LIST_ITEMS = 1000

HTTP_IGNORE_METHODS = {'CONNECT', 'HEAD', 'OPTIONS', 'TRACE'}
HTTP_READ_METHODS = {'GET'}
HTTP_WRITE_METHODS = {'DELETE', 'PATCH', 'POST', 'PUT'}

# todo; this could be a config file
OBJECT_TEMPLATE = {
    "project": {
        "Sections": [
            {
                "app": {
                    "states": {
                        "load": {
                            "url": "http://google.com"
                        }
                    },
                    "url": "OVE_APP_HTML"
                },
                "space": "SPACE_NAME",
                "h": 1080,
                "w": 1920,
                "x": 0,
                "y": 0
            }
        ]
    }
}

DEFAULT_AUTH_GROUPS = {"groups": ["public"]}
