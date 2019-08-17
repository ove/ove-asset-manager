# Development Guide

## Starting the services locally

Please refer to the [local install guide](Install.md#installation-for-a-non-docker-environment) to start the development.

## Dependencies

All AM services use the following libraries:
- [falcon](https://falconframework.org/) ([docs](https://falcon.readthedocs.io/en/stable)) - for the REST API
- [gunicorn](https://gunicorn.org/) - as the production web server
- [urllib3](https://urllib3.readthedocs.io/en/latest/) - as a REST client

Backend and workers only:
- [minio](https://www.minio.io/) - as an Amazon S3 compatible object store

UI only:
- [Jinja2](http://jinja.pocoo.org/docs/2.10/) - for HTML templating
- [markdown2](https://github.com/trentm/python-markdown2) - converting the worker documentation from Markdown to HTML

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
- ***_utils.py**: utils classes for alerts or Jinja2 integration
- **backend.py**: the client used to make requests to the backend
- **controller.py**: the UI controller which connects the mangers to the API routes
- **routes.py**: all the REST routes, in falcon format ([falcon docs on routing](https://falcon.readthedocs.io/en/stable/api/routing.html))
- **middleware.py**: a content type validator

The [Jinja2](http://jinja.pocoo.org/docs/2.10/) templates written in HTML and are located in the **ui/templates**.

The frontend uses a few JavaScript libraries. If you add new dependencies, then these must be added to **package.json**
and the assets (js, css and font files exposed by the library) must be added to **move-assets.js**.

You may find it convenient to set the `SERVICE_AM_HOSTNAME` environment variable to point at an instance of the AM backend running on a different machine during development and testing.

## Adding a new Worker

Creating a worker requires changes in several places:

* a Markdown documentation file in `docs/workers`
* a Dockerfile in a new subdirectory of `docker/`
* the worker itself, in a new subdirectory of `workers/`
* an addition to `docker-compose.yml`

You will also need to modify the ` 	docker-compose.am.yml` template used by the
[OVE Installer](https://github.com/ove/ove-install).

All new workers can extend the `BaseWorker` class. The methods that require an implementation
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
        see http://www.alpacajs.org/ for more details
        """
        return {}

    def process(self, project_id: str, meta: OveMeta, options: Dict):
        """
        Override this to start processing
        :param project_id: name of the project to process
        :param meta: the object to process
        :param options: task options, passed by the asset manager. Can be empty
        :return: None
        :raises: Any exception is treated properly and logged by the safe_process method
        """
        pass
        # this is where the worker processing happens
```

To test a worker using Docker, you will need to expose the correct port (e.g, with `-p 6090:6090`), and set the
environment variables `SERVICE_AM_HOSTNAME`, `SERVICE_AM_PORT`, and `SERVICE_HOSTNAME`. If testing with an instance of
the Asset Manager on another machine, that machine must be able to resolve the `SERVICE_HOSTNAME` to the machine running
the worker.
