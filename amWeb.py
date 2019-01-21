# Web interface for users to upload and manage assets from using flask
# This is deprecated with the Falcon version
# Requires pip install flask

from flask import Flask, abort, jsonify
from flask import request
import fileStoreInterpret
import json


class ProjectsList:
    def __init__(self):
        self.Projects = []


class AssetsList:
    def __init__(self):
        self.Assets = []


app = Flask(__name__)


# Current route
@app.route('/')
def webIndex():
    return 'Welcome to the OVE Asset Manager'


# Lists all file stores
@app.route('/api/list')
def storesPrintAll():
    return "Not yet implemented"


# Lists all buckets (projects) in an object store - returns JSON array
@app.route('/api/<string:store_id>/list', methods=['GET'])
def projectsPrintAll(store_id):
    bucketList = fileStoreInterpret.listProjects(store_id)
    formJson = ProjectsList()
    for bucketElements in bucketList:
        formJson.Projects.append(bucketElements)
    bucketListHttp = json.dumps(formJson.__dict__)

    return bucketListHttp


# Lists all assets in a project - returns JSON array
@app.route('/api/<string:store_id>/<string:project_id>/list', methods=['GET'])
def assetsPrintAll(store_id, project_id):
    projectList = fileStoreInterpret.listAssets(store_id, project_id)
    formJson = AssetsList()
    for projectElements in projectList:
        formJson.Assets.append(projectElements)
    projectListHttp = json.dumps(formJson.__dict__)

    return projectListHttp


# Shows the meta data for an asset - returns JSON object
@app.route('/api/<string:store_id>/<string:project_id>/<string:asset_id>/meta', methods=['GET'])
def assetMetaAll(store_id, project_id, asset_id):
    assetMeta = fileStoreInterpret.showMeta(store_id, project_id, asset_id)
    formJson = assetMeta
    return formJson


# Creates a project/bucket - returns boolean of success
@app.route('/api/<string:store_id>/create', methods=['POST'])
def projectCreate(store_id):
    if not request.json or not 'name' in request.json:
        return abort(400)
    newProject = {
        'name': request.json['name'],
        'description': request.json.get('description', ""),
    }
    newProjectName = newProject['name']
    print(newProjectName)
    createProject = fileStoreInterpret.createProject(store_id, newProjectName)
    if createProject[0] == False and createProject[1] == "This project name already exists":
        return abort(409)
    else:
        return abort(400, createProject[1])
    return jsonify({'Project': newProjectName}), 201
