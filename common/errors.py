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

    def __str__(self) -> str:
        return "{}(title='{}', description='{}')".format(self.__class__.__name__, self.title, self.description)

    def __repr__(self) -> str:
        return "{}(title='{}', description='{}')".format(self.__class__.__name__, self.title, self.description)


class MissingParameterError(ValidationError):
    def __init__(self, name: str):
        super(MissingParameterError, self).__init__(title="Missing {}".format(name),
                                                    description="The {} parameter is required".format(name))


class InvalidNameError(ValidationError):
    def __init__(self, name: str):
        super(InvalidNameError, self).__init__(title="Invalid name {}".format(name),
                                               description="Please check you have no invalid characters")


class ProjectExistsError(ValidationError):
    def __init__(self, store_name: str, project_name: str):
        description = "The project '{}' already exists in store '{}'".format(project_name, store_name)
        super(ProjectExistsError, self).__init__(title="Project already in use", description=description)


class AssetExistsError(ValidationError):
    def __init__(self, store_name: str, project_name: str = None, asset_name: str = None):
        description = "The asset '{}' already exists in project '{}' on '{}'".format(asset_name, project_name, store_name)
        super(AssetExistsError, self).__init__(title="Asset already in use", description=description)


class InvalidStoreError(ValidationError):
    def __init__(self, name: str):
        super(InvalidStoreError, self).__init__(title="The provided store '{}' is invalid".format(name),
                                                description="The store may not exist or you don't have access to it")


class InvalidAssetError(ValidationError):
    def __init__(self, store_name: str, project_name: str, asset_name: str):
        description = "Error while trying to retrieve asset '{}' from project '{}' on '{}'".format(store_name, project_name, asset_name)
        super(InvalidAssetError, self).__init__(title="The provided asset '{}' is invalid".format(asset_name),
                                                description=description)


class InvalidObjectError(ValidationError):
    def __init__(self, store_name: str, project_name: str, object_name: str):
        description = "Error while trying to retrieve object '{}' from project '{}' on '{}'".format(store_name, project_name, object_name)
        super(InvalidObjectError, self).__init__(title="The provided object name '{}' is invalid".format(object_name),
                                                 description=description)


class ObjectExistsError(ValidationError):
    def __init__(self, store_name: str, project_name: str = None, object_name: str = None):
        description = "The object '{}' already exists in project '{}' on '{}'".format(store_name, project_name, object_name)
        super(ObjectExistsError, self).__init__(title="Object already in use", description=description)


class InvalidDataError(ValidationError):
    def __init__(self):
        super(InvalidDataError, self).__init__(title="Invalid data", description="The data provided has an invalid format")


class WorkerExistsError(ValidationError):
    def __init__(self):
        super(WorkerExistsError, self).__init__(title="Worker already in use", description="Please use the patch method to update workers")


class WorkerNotFoundError(ValidationError):
    def __init__(self):
        super(WorkerNotFoundError, self).__init__(title="Worker not found", description="Please add the worker first")


class WorkerCallbackError(ValidationError):
    def __init__(self, url: str):
        super(WorkerCallbackError, self).__init__(title="Worker callback not reachable", description="'{}' is not reachable".format(url))


class WorkerUnavailableError(ValidationError):
    def __init__(self, filename: str):
        super(WorkerUnavailableError, self).__init__(title="No worker available for task",
                                                     description="'{}' cannot be processed by any worker".format(filename))


class WorkerLockError(ValidationError):
    def __init__(self):
        super(WorkerLockError, self).__init__(title="Cannot lock worker", description="The asset has already a worker assigned")
