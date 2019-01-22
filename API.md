**OVE Asset Manager RESTful documentation**
----
  _This API is designed to allow you to perform the majority of necessary file operations using a RESTful API_

----

* **/liststore**

    _Lists available file stores_

* **Method:**

    `GET` 

* **Success Response:**
  
  * **Code:** 200 <br />
    **Content:** `Not yet implemented`
 
* **Error Response:**


  * **Code:** 400 BAD REQUEST <br />
    **Content:** `Not yet implemented`

* **Notes:**

    _This is not yet implemented_
    
----

* **/{storeid}/list**

    _Lists available projects in a file store_

* **Method:**

    `GET`

* **Success Response:**
  
  * **Code:** 200 <br />
    **Content:** `{ "Projects" : ["project1"] }`
 
* **Error Response:**

  * **Code:** 404 DOES NOT EXIST <br />
    **Content:** `{Store does not exist}`


----

* **/{storeid}/create**

  <_The URL Structure (path only, no root url)_>

* **Method:**
    
    `POST`

* **Data Params**

    `Requires JSON body`
    
    `{
	"name":"projectname"
    }`
* **Success Response:**
  
  * **Code:** 200 <br />
    **Content:** `{
    "Project": "projectname"
    }`
 
* **Error Response:**
    
  * **Code:** 400 BAD REQUEST <br />
    **Content:** `{
  "title": "400 Bad Request",
  "description": "There was an error creating your project, please check your name"
}`

  * **Code:** 409 CONFLICT <br />
    **Content:** `{ Project of that name already exists}`

* **Notes:**

    _With S3 storage, the project name must conform to s3 bucket name conventions_
    
----

* **/{storeid}/{projectname}/list**

    _Lists available assetss in a file store_

* **Method:**

    `GET`

* **Success Response:**
  
  * **Code:** 200 <br />
    **Content:** `{ "Assets" : ["Asset1"] }`
 
* **Error Response:**

  * **Code:** 404 DOES NOT EXIST <br />
    **Content:** `{Project does not exist}`

