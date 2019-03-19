# Open Visualisation Environment - Asset Manager and Proxy

This repository contains an Asset Manager (AM) to manage data sets for access to an installation of 
[Open Visualisation Environment (OVE)](https://github.com/ove/ove), as well as a high speed 
proxy to provide authenticated access to data from a range of sources.

[//]: # (These are then authenticated through the Authentication manager in order to ensure no direct access to a data set by unauthenticated users.)

## Concepts

The Asset Manager stores files in an S3 compatible object **Store**, such as [Minio](http://minio.io).
One instance of the Asset Manager can work with multiple stores.

An **Asset** is a collection of one or more **files** that can be treated as a single unit and versioned, processed
and displayed together. Each asset has associated metadata (e.g. processing state, name, description, tags, etc.).

Assets (and non-asset objects in JSON format) can be grouped together into a **Project**.
While the AM does not assign any specific meaning to a project, and allows you to group assets by any criteria, other
tools may interpret projects as indicating that particular content should be displayed together (e.g., a gallery might
display all of the assets in a selected project).

Each time any file in an asset is updated, a new **Version** of the whole asset is recorded. Previous versions of the
asset are retained, and can still be accessed.

**Workers** can be scheduled to asynchronously perform a task performed on a file, such as converting it to a new file
format. Workers operate non-destructively and do not modify or delete uploaded files, so do not create new versions of
an asset when they run.
 

## Components

The Asset Manager is split into 3 parts:

- The **Backend** exposes a full [RESTful API](docs/API.md) for operations on projects, assets and files.
This service can work independently from all the other services.
- The **Read proxy** exposes an HTTP endpoint to read individual files off the object store.
The AM Read Proxy is authenticated by the same rules as the Backend service.
- The **UI** exposes a User Interface for most of the operations performed by the Backend service.
- The **Workers** asynchronously perform additional tasks on assets:
    - **Unzip**: please see the [worker documentation](docs/workers/ZipWorker.md) for more details  
    - **DeepZoomImage**: please see the [worker documentation](docs/workers/DeepZoomImageWorker.md) for more details  
    - **Tulip network layout**: please see the [worker documentation](docs/workers/Tulip.md) for more details

## Install

Please check the [Install Guide](docs/Install.md) for more details.

## Development

Please see the [Development Guide](docs/Development.md) for more details.
