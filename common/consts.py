DEFAULT_CREDENTIALS_CONFIG = "config/credentials.json"
DEFAULT_AUTH_CONFIG = "config/auth.json"
DEFAULT_WORKER_CONFIG = "config/worker.json"

CONFIG_STORE_DEFAULT = "default"
CONFIG_STORES = "stores"
CONFIG_STORE_NAME = "name"
CONFIG_ENDPOINT = "endpoint"
CONFIG_ACCESS_KEY = "accessKey"
CONFIG_SECRET_KEY = "secretKey"
CONFIG_PROXY_URL = "proxyUrl"

CONFIG_AUTH_JWT = "jwt"
CONFIG_AUTH_JWT_SECRET = "secret"

CONFIG_MONGO = "mongo"
CONFIG_MONGO_HOST = "host"
CONFIG_MONGO_PORT = "port"
CONFIG_MONGO_USER = "user"
CONFIG_MONGO_PASSWORD = "password"
CONFIG_MONGO_DB = "db"
CONFIG_MONGO_MECHANISM = "mechanism"
CONFIG_MONGO_AUTH_COLLECTION = "collection"
CONFIG_MONGO_WORKER_COLLECTION = "workerCollection"
CONFIG_MONGO_QUEUE_COLLECTION = "workerQueue"

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
