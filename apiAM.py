# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd


import falcon
import fileStoreInterpret
import json


class AssetListJson:
    def __init__(self):
        self.Assets = []


class ProjectListJson:
    def __init__(self):
        self.Projects = []


class APIList(object):
    def on_get(self, req, resp):
        resp.body = 'Not yet implemented'
        resp.status = falcon.HTTP_200


class ProjectList(object):
    def on_get(self, req, resp, store_id):
        bucketList = fileStoreInterpret.listProjects(store_id)
        formJson = ProjectListJson()
        for bucketElements in bucketList:
            formJson.Projects.append(bucketElements)
        bucketListHttp = json.dumps(formJson.__dict__)
        resp.body = bucketListHttp
        resp.status = falcon.HTTP_200

class ProjectCreate(object):
    def on_post(self, req, resp, store_id):
        try:
            newData = json.loads(req.stream.read().decode('utf-8'))
            newProjectName = newData['name']
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name', 'A Project name is required')

        try:
            createProject = fileStoreInterpret.createProject(store_id, newProjectName)
            if createProject[0] is False and createProject[1] == "This project name already exists":
                raise falcon.HTTPConflict('This project name is already in use')
            elif createProject[0] is False:
                raise falcon.HTTPBadRequest(createProject[1])
        except KeyError:
            raise falcon.HTTPBadRequest('This went really badly wrong')

        resp.body = json.dumps({'Project': newProjectName})
        resp.status = falcon.HTTP_200

class AssetList(object):
    def on_get(self, req, resp, store_id, project_id):
        projectlist = fileStoreInterpret.listAssets(store_id, project_id)
        formJson = AssetListJson()
        for projectElements in projectlist:
            formJson.Assets.append(projectElements)
        projectlistHttp = json.dumps(formJson.__dict__)
        resp.body = projectlistHttp
        resp.status = falcon.HTTP_200

class AssetCreate(object):
    def on_post(self,req,resp,store_id,project_id):
        try:
            newData = json.loads(req.stream.read().decode('utf-8'))
            newAssetName = newData['name']
            print(newAssetName)
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name','An Asset name is required')
        try:
            createAsset = fileStoreInterpret.createAsset(store_id,project_id,newAssetName)
            if createAsset[0] is False and createAsset[1] == "This asset name already is in use":
                raise falcon.HTTPConflict('This asset name is already in use')
            elif createAsset[0] is False:
                raise falcon.HTTPBadRequest(createAsset[1])
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')

        resp.body = json.dumps({'Asset':newAssetName})
        resp.status = falcon.HTTP_200


app = falcon.API()

app.add_route('/api/list', APIList())
app.add_route('/api/{store_id}/list', ProjectList())
app.add_route('/api/{store_id}/{project_id}/list', AssetList())
app.add_route('/api/{store_id}/create', ProjectCreate())
app.add_route('/api/{store_id}/{project_id}/create',AssetCreate())


# Shows the meta data for an asset - returns JSON object
def assetMetaAll(store_id, project_id, asset_id):
    assetMeta = fileStoreInterpret.showMeta(store_id, project_id, asset_id)
    formJson = assetMeta
    return formJson
