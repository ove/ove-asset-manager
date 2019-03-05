# Open Visualisation Environment - Asset Manager and Proxy

This repository contains an Asset Manager (AM) to manage data sets for access to an installation of 
[Open Visualisation Environment (OVE)](https://github.com/ove/ove), as well as a high speed 
proxy to provide authenticated access to data from a range of sources.

[//]: # (These are then authenticated through the Authentication manager in order to ensure no direct access to a data set by unauthenticated users.)

## Concepts

- **Store** - is the storage engine where all the files/objects are stored. The AM currently uses an S3 
compatible object store, such as [MINIO](http://minio.io). The AM supports working with multiple stores 
at the same time.
- **Project** - is a collection of assets and project-level objects in json format that can be grouped together. 
While the AM does not assign any semantic to the project files so they can be grouped by any criteria, OVE 
may use projects to group content displayed together (e.g. gallery projects).
- **Asset** - is usually a collection of one or more files that can be treated as an unit: versioned, processed
 and displayed together. Each asset contains metadata on current handling of the object (e.g. processing state, 
 name, description, tags, etc.)
- **File** - an object stored as part of an asset
- **Version** - asset files are versioned together every time an update occurs
- **Worker** - an async task performed on an asset to transform the original file format into new formats. The
files created by the worker are not considered to be updates as all the worker operations are non-destructive.   
 

## Components

The service is split into 3 parts:

- AM Backend - a service that exposes a full [restful API](docs/API.md) for all 
the operations on projects, assets and files. This service can work independently from all 
the other services.  
- AM Read proxy - a service that exposes a http endpoint used to read individual files off the object store.
The AM Read Proxy is authenticated by the same rules as the Backend service.  
- AM UI - a service that exposes an UI for most of the operations performed by the Backend service.
- AM Workers - async workers to perform additional tasks on assets (e.g. Unzip, Deep Zoom Image creation):
    - **Unzip**: please see the [worker documentation](docs/workers/ZipWorker.md) for more details  
    - **DeepZoomImage**: please see the [worker documentation](docs/workers/DeepZoomImageWorker.md) for more details  

## Install

Please check the [Install Guide](docs/Install.md) for more details.

## Development

Please see the [Development Guide](docs/Development.md) for more details.