import logging

import falcon


def handle_exceptions(ex: Exception, _req: falcon.Request, _resp: falcon.Response, _params):
    logging.debug("Handling exception: %s", repr(ex))

    if isinstance(ex, falcon.HTTPError):
        raise ex

    if isinstance(ex, (AssetExistsError, ObjectExistsError)):
        raise falcon.HTTPConflict(title=ex.title, description=ex.description)

    if isinstance(ex, ValidationError):
        raise falcon.HTTPBadRequest(title=ex.title, description=ex.description)

    raise falcon.HTTPBadRequest(title="Internal Server error", description=str(ex))


class ValidationError(Exception):
    def __init__(self, description: str, title: str = "Internal Server error"):
        self.title = title
        self.description = description


class MissingParameterError(ValidationError):
    def __init__(self, name: str):
        super(MissingParameterError, self).__init__(title="Missing {}".format(name),
                                                    description="The {} is required".format(name))


class AssetExistsError(ValidationError):
    def __init__(self, store_name: str, project_name: str = None, asset_name: str = None):
        description = "store = '{}' project = '{}' asset = '{}'".format(store_name, project_name, asset_name)
        super(AssetExistsError, self).__init__(title="Asset already in use", description=description)


class InvalidStoreError(ValidationError):
    def __init__(self, name: str):
        super(InvalidStoreError, self).__init__(title="The provided store '{}' is invalid".format(name),
                                                description="The store may not exist or you don't have access to it")


class InvalidAssetError(ValidationError):
    def __init__(self, store_name: str, project_name: str, asset_name: str):
        description = "store = '{}' project = '{}' asset = '{}'".format(store_name, project_name, asset_name)
        super(InvalidAssetError, self).__init__(title="The provided asset '{}' is invalid".format(asset_name),
                                                description=description)


class InvalidObjectError(ValidationError):
    def __init__(self, store_name: str, project_name: str, object_name: str):
        description = "store = '{}' project = '{}' object = '{}'".format(store_name, project_name, object_name)
        super(InvalidObjectError, self).__init__(title="The provided object name '{}' is invalid".format(object_name),
                                                 description=description)


class ObjectExistsError(ValidationError):
    def __init__(self, store_name: str, project_name: str = None, object_name: str = None):
        description = "store = '{}' project = '{}' object = '{}'".format(store_name, project_name, object_name)
        super(ObjectExistsError, self).__init__(title="Object already in use", description=description)
