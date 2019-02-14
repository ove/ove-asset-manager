# Open Visualisation Environment - Asset Manager and Proxy

This repository contains an Asset Manager to manage data sets for access to an installation of [Open Visualisation Environment (OVE)](https://github.com/ove/ove), as well as a high speed proxy to provide authenticated access to data from a range of sources.

These are then authenticated through the Authentication manager in order to ensure no direct access to a data set by unauthenticated users.

The model for file storage consists of the following:

 + OVEconfig folder
 	- This lists the available projects, and permissions for each project
 	- This will be generated on a new file store or can be generated if one does not already exist
 + Project folders
 	- These are handled as buckets on object stores
 	- Each contains a config file listing the meta data and asset data for each project
 + Asset folder
 	- These are sub folders within a project
 	- Each contains a config file with meta data on current handling for an asset (e.g. processing state)


The RESTful API takes the format:

`api/store_name/project_name/asset_name/operation`

For more details see the [API documentation](API.md).
