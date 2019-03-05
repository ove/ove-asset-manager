# Development guide

## Starting the services locally

Please refer to the [local install guide](Install.md#non-docker-installs) to start the development.

## Dependencies

All AM services use the following libraries:
- falcon - for the REST Api
- gunicorn - as the production web server
- requests and urllib3 - as a REST client

Backend and workers only: 
- minio - for the s3 api compatibility

UI only:
- Jinja2 - for html templating
- markdown2 - for markdown to html conversion of the worker documentation

## Adding new AM Backend functionality

The code for the AM Backend can be found in the **am** module:

- **__init__.py**: is used to configure the app and setup all the app routes
- **__main__.py**: a startup script that can be used for development and testing
- **controller.py**: the backend controller which connects the mangers to the API routes
- **managers.py**: the worker manager, keeping the state of all registered workers
- **routes.py**: all the REST routes, in falcon format

## Adding new UI functionality

The code for the AM Backend can be found in the **ui** module:

- **__init__.py**: is used to configure the app and setup all the app routes
- **__main__.py**: a startup script that can be used for development and testing
- **backend.py**: the UI controller which connects the mangers to the API routes
- ***_utils.py**: utils classes for alerts or jinja2 integration
- **backend.py**: the client used to make requests to the backend 
- **controller.py**: the UI controller which connects the mangers to the API routes
- **routes.py**: all the REST routes, in falcon format
- **middleware.py**: a content type validator

The Jinja2 templates written in html and are located in the **ui/templates**.

The frontend uses a few javascript libraries. All these have to be added in **package.json** 
and the assets (js, css and fonts exposed by the library) need to be added to **move-assets.js**.

## Adding a new Worker

All new workers can extend the BaseWorker class. The methods that require an implementation
are marked as abstract in the base class:

```python
from typing import List, Dict
from common.entities import OveMeta

from workers.base import BaseWorker

class NewWorker(BaseWorker):
    def worker_type(self) -> str:
        """
        :return: the worker type as a string. This value can be a valid WorkerType or anything else
        """
        return ""

    def extensions(self) -> List:
        """
        :return: the extensions handled by this worker
        """
        return []

    def description(self) -> str:
        """
        :return: description in human-readable format
        """
        return ""

    def docs(self) -> str:
        """
        :return: the worker documentation document url, in markdown format
        see https://github.com/trentm/python-markdown2 for more details
        """
        return ""

    def parameters(self) -> Dict:
        """
        :return: the worker parameter description, in json-form format:
        see https://github.com/jsonform/jsonform for more details
        """
        return {}

    def process(self, project_name: str, meta: OveMeta, options: Dict):
        """
        Override this to start processing
        :param project_name: name of the project to process
        :param meta: the object to process
        :param options: task options, passed by the asset manager. Can be empty
        :return: None
        :raises: Any exception is treated properly and logged by the safe_process method
        """
        pass
        # this is where the worker processing happens
```