# OVE Asset Manager REST API documentation

This API is designed to allow you to perform the majority of necessary file operations using a REST API

----
- **/api/list**: 
    - `GET`:  _Lists available file stores_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `['store1', 'store2', '...']` 
----

- **/api/{store_id}/list**
    - `GET`: _Lists available projects in a file store_
    - **Query params:** `metadata=true | false` - optional, if true the project list include some metadata
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `[{name: "project1", "creationDate": "date"}, "..."]` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
----

- **/api/{store_id}/create**
    - `POST`: _Create project_
    - **Data Params:** `Requires JSON body`
    
    `{
	"name":"project_name"
    }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{'Project': project_name}` 
        - **Error**: Store not found <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Error**: Project already exists <br />
        **HTTP Code:** 409 Conflict <br />
        **Content:** `{title="Project already in use", description="..."}`
    * **Notes:** _With S3 storage, the project name must conform to s3 bucket name conventions_
----

- **/api/{store_id}/{project_name}/list**
    - `GET`: _Lists available assets in a file store with meta data_
    - **Query params:** 
        - `includeEmpty=(True|False)` - optional, if true all folders are included regardless of whether they are ove assets`
        - `filterByTag=<tag_name>` - optional, filter all assets tagged by tag_name 
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ "Assets" : ["Asset1"] }` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
----

* **/api/{store_id}/{project_name}/create**
    - `POST`: _Create asset_
    - **Data Params:** `Requires JSON body`
    
    `{
	"name":"asset_name"
    }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{'Asset': asset_name}` 
        - **Error**: Store not found <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Error**: Asset already exists <br />
        **HTTP Code:** 409 Conflict <br />
        **Content:** `{title="Asset already in use", description="..."}`
    * **Notes:** _With S3 storage, asset name is not allowed to contain / or any restricted asset names (e.g. new, .ovemeta, list, create)
----

- **/api/{store_id}/{project_name}/object/{object_id}**
    - `HEAD`: _Check if an object exists_
    - **Response:**
        - **Success**: HTTP Code 200
        - **Not found**: HTTP Code 404
    - `GET`: _Get an object in JSON format_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ ... }` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Object not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Object not found", description="..."}`
    - `POST`: _Create an object in JSON format_
    - **Data Params:** `{ ... }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ ... }` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Object not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Object not found", description="..."}`
        - **Object already in use**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Object already in use", description="..."}`
    - `PUT`: _Update an object in JSON format_
    - **Data Params:** `{ ... }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ ... }` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Object not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Object not found", description="..."}`
----

- **/api/{store_id}/{project_name}/object/{object_id}/info**
    - `GET`: _Get the object metadata_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ name="...", index_file="..."}` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Object not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Object not found", description="..."}`
----

- **/api/{store_id}/{project_name}/meta/{asset_id}**
    - `HEAD`: _Check if an asset exists_
    - **Response:**
        - **Success**: HTTP Code 200
        - **Not found**: HTTP Code 404
    - `GET`: _Get an asset metadata_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{
            "name": "...",
            "project": "...",
            "description": "...",
            "index_file": "...",
            "version": "...",
            "history": "...",
            "tags": "...",
            "worker": "...",
            "processing_status": "...",
            "processing_error": "..."
        }` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
    - `POST`: _Update a project metadata_
    - **Data Params:** `{"description": "...", "tags": "..."}`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{"Status": "OK"}`  
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
----  

- **/api/{store_id}/{project_id}/files/{asset_id}**
    - `GET`: _list of files under the current version of the asset_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `[{name: "...", url: "..."}]` 
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
----        

- **/api/{store_id}/{project_name}/upload/{asset_id}**
    - `POST`: _Upload an asset_
    - **Headers:** `content-disposition: filename="<file_name>"`
    - **Body:** `the file octet stream`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{"Status": "OK"}`  
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
        - **Asset exists**: <br />
        **HTTP Code:** 409 Conflict <br />
        **Content:** `{title="Asset exists", description="..."}`
----        

- **/api/{store_id}/{project_name}/update/{asset_id}**
    - `POST`: _Update an asset file_
    - **Headers:** `content-disposition: filename="<file_name>"`
    - **Body:** `the file octet stream`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{"Status": "OK"}`  
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
----

- **/api/{store_id}/{project_name}/createUpload/{asset_id}**
    - `POST`: _Create an asset and upload the file content_
    - **Headers:** `content-disposition: filename="<file_name>"`
    - **Body:** `the file octet stream`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{"Status": "OK"}`  
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
----

- **/api/{store_id}/{project_name}/process/{asset_id}**
    - `POST`: _Schedule a worker processing task on the selected asset_
    - **Data Params:** `{"worker_type": "...",}`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{"Status": "OK"}`  
        - **Store not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Store not found", description="..."}`
        - **Project not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Project not found", description="..."}`
        - **Asset not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Asset not found", description="..."}`
        - **Worker not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Worker not found", description="..."}`
----

- **/api/workers**
    - `GET`: _Worker list_
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `['worker1', ...]` 
    - `POST`: _Register worker_
    - **Data Params:** `{
            "name": "...",
            "type": "...",
            "description": "...",
            "extensions": "...",
            "status": "...",
            "callback": "...",
            "status_callback": "...",
            "parameters": "...",
            "docs": "..."
        }` 
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{
            "name": "...",
            "type": "...",
            "description": "...",
            "extensions": "...",
            "status": "...",
            "callback": "...",
            "status_callback": "...",
            "parameters": "...",
            "docs": "..."
        }` 
        - **Worker already exists**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Worker already exists", description="..."}`
    - `PATCH`: _Update the status of a worker_
    - **Data Params:** `{ name: "...", status: "..." }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ 'Status': 'OK' }` 
        - **Worker not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Worker not found", description="..."}`
    - `DELETE`: _Unregister a worker_
    - **Data Params:** `{ name: "..." }`
    - **Response:**
        - **Success**: <br />
        **HTTP Code:** 200 <br />
        **Content:** `{ 'Status': 'OK' }` 
        - **Worker not found**: <br />
        **HTTP Code:** 400 Bad Request <br />
        **Content:** `{title="Worker not found", description="..."}`    
----