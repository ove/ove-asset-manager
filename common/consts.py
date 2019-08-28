DEFAULT_CONFIG = "config/credentials.json"

CONFIG_STORE_DEFAULT = "default"
CONFIG_STORES = "stores"
CONFIG_STORE_NAME = "name"
CONFIG_ENDPOINT = "endpoint"
CONFIG_ACCESS_KEY = "accessKey"
CONFIG_SECRET_KEY = "secretKey"
CONFIG_PROXY_URL = "proxyUrl"

OVE_META = ".ovemeta"
PROJECT_FILE = "project.json"

PROJECT_METADATA_SECTION = "Metadata"
PROJECT_BASIC_TEMPLATE = {PROJECT_METADATA_SECTION: {}, 'Sections': []}

S3_SEPARATOR = "/"

S3_OBJECT_EXTENSION = ".json"

MAX_LIST_ITEMS = 1000

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
