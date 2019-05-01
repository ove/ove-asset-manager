# Usage Tutorial

<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">

The OVE asset manager interface presents two main views: a table of workers, and a hierarchy of *stores*, *projects* and *assets*, each represented by a table.


## Managing Workers

Workers are separate programs that can asynchronously process files (e.g., to convert it to a new file format, expand a zip archive, or apply a layout algorithm to a file describing a network).

When a worker program starts running, it automatically *registers* itself with the Asset Manager using a REST API. 
Multiple instances of the same `type` of worker can register with the same instance of the Asset Manager.

![](data:image/png;base64,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)

The status column indicates whether the worker instance is `ready` (<i class='fa fa-check-circle icon-success'></i>), currently `processing` a file (<i class='fa fa-spinner'></i>), or has encountered an `error` (<i class='fa-exclamation-circle icon-error'></i>); worker status can be reset to `ready` by clicking on the <i class='fa-sync fa'></i> button.

A worker should automatically de-register itself when it stops running, but it is also possible to manually de-register a worker by clicking on the button with a <i class='fa fa-trash-alt'></i> icon.

The documentation for a worker can be viewed by clicking on the <i class='fa-book fa'></i> button.


## Managing projects and assets

The **home page** displays a list of S3 compatible object *stores*; selecting a store opens a list of the *projects* it contains.


### Project list

You can create a new project by typing its name into the input box and pressing the <i class='fa-folder-plus fa'></i> button.

From the **project list**, you can edit the details of a project by clicking on the <i class='fa-edit fa-w-18'></i> icon, or list the **assets** in the project by clicking on either the project name or the <i class='fa-edit fa-w-18'></i> icon.


### Asset list

From a project's **asset list**, you can add assets to a project in one of two ways:

* You can click on the `Upload` button, and select one or more files to upload. An asset will be automatically created for each file, with an asset name determined by the filename.

* Alternatively, you can manually create an asset by clicking on the `New Asset` button, enter the asset name, and click `Save`. 
You can then add an asset to this file from the Edit Asset page, which the asset creation page will automatically redirect to after it is submitted, or by clicking the upload icon (<i class= 'fa-upload fa'></i>)
Regardless of how the asset was originally created, you can use these methods to upload a modified file. 

A worker can be instructed to process an asset by clicking on the <i class=fa-paint-roller fa> button.

After being processed by a worker, an asset may contain multiple files (e.g., because a zip file has been expanded into a directory, or because an image has been decomposed into tiles). 
Clicking the <i class='fa-list-alt fa'></i> icon lists the contents of an asset, with a link that allows each to be opened.
Regardless of the number of a files in an asset, there will be a single file designated as the *Index File*; a link to this is provided in a column of the asset table.

As well as assets, a project can contain a *project file*, which explains how its assets should be displayed by OVE.
This file can be edited (or created if it does not yet exist) by clicking on the `Edit project file` button above the table.
