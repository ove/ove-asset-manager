# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd


import falcon
import fileStoreInterpret
import tempfile
import re

assetDescription = "Placeholder Asset description"


class oveMeta:
    def __init__(self):
        self.name = ''
        self.description = ''
        self.uploaded = False
        self.permissions = ''

    def setName(self,name):
        self.name = name

    def setDescription(self,description):
        self.description = description

    def isUploaded(self,upload):
        self.uploaded = upload

    def setPermissions(self,perms):
        self.permissions = perms


def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


class StoreList(object):
    def on_get(self, req, resp):
        resp.body = 'Listing of available file stores is not yet implemented'
        resp.status = falcon.HTTP_200

class WorkersList(object):
    def on_get(self, req, resp):
        resp.body = 'Listing of available file workers is not yet implemented'
        resp.status = falcon.HTTP_200

class ProjectList(object):
    def on_get(self, req, resp, store_id):
        bucketList = fileStoreInterpret.listProjects(store_id)
        resp.media = bucketList
        resp.status = falcon.HTTP_200


class ProjectCreate(object):
    def on_post(self, req, resp, store_id):
        try:
            newProjectName = req.media.get('name')
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name', 'A Project name is required')

        try:
            createProject = fileStoreInterpret.createProject(store_id, newProjectName)
            if createProject[0] is False and createProject[1] == "This project name already exists":
                raise falcon.HTTPConflict('This project name is already in use')
            elif createProject[0] is False:
                print (createProject[1])
                raise falcon.HTTPBadRequest("400 Bad Request",
                                            "There was an error creating your project, please check your name")
        except KeyError:
            raise falcon.HTTPBadRequest('This went really badly wrong')

        resp.media = {'Project': newProjectName}
        resp.status = falcon.HTTP_200


class AssetList(object):
    def on_get(self, req, resp, store_id, project_id):
        assetList = fileStoreInterpret.listAssets(store_id, project_id)
        resp.media = assetList
        resp.status = falcon.HTTP_200


class AssetCreate(object):
    def on_post(self,req,resp,store_id,project_id):
        try:
            newAssetName = req.media.get('name')
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name', 'A valid asset name is required')
        try:
            meta = oveMeta()
            meta.setName(newAssetName)
            meta.setDescription(assetDescription)
            createAsset = fileStoreInterpret.createAsset(store_id,project_id,meta)
            if createAsset[0] is False and createAsset[1] == "This asset already exists":
                raise falcon.HTTPConflict("This asset already exists")
            elif createAsset[0] is False:
                print(createAsset[1])
                raise falcon.HTTPBadRequest("There was an error creating your asset")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')

        resp.media = {'Asset':newAssetName}
        resp.status = falcon.HTTP_200


class AssetUpload(object):
    def on_post(self,req,resp,store_id,project_id,asset_id):
        try:
            # retrieve the existing meta data
            meta = oveMeta()
            getmeta = fileStoreInterpret.getAssetMeta(store_id, project_id, asset_id,meta)
            if getmeta[0] is False:
                raise falcon.HTTPBadRequest("You have not created this asset yet")
            if getmeta[1].uploaded is True:
                raise falcon.HTTPConflict("This asset already has a file - if you wish to change this file, use update")
            if req.get_header('content-disposition') is not None:
                fname = re.findall("filename=(.+)", req.get_header('content-disposition'))
                if is_empty(fname) is True:
                    raise falcon.HTTPInvalidHeader("No filename specified in header", 'content-disposition')
                fname = fname[0]
                fname = (fname.encode('ascii',errors='ignore').decode()).strip('\"')
                if fname == '.ovemeta':
                    raise falcon.HTTPForbidden("403 Forbidden",
                                               "This is a reserved filename and is not allowed as an asset name")
            else:
                    raise falcon.HTTPBadRequest("No filename specified -"
                                                " this should be in the content-disposition header")
            with tempfile.NamedTemporaryFile() as cache:
                cache.write(req.stream.read())
                cache.flush()
                meta = getmeta[1]
                fileStoreInterpret.uploadAsset(store_id,project_id,asset_id,fname,meta,cache)
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')
        resp.media = {'Asset': fname}
        resp.status = falcon.HTTP_200


class MetaEdit(object):
    def on_get(self,req,resp,store_id,project_id,asset_id):
        try:
            meta = oveMeta()
            getmeta = fileStoreInterpret.getAssetMeta(store_id,project_id,asset_id,meta)
            if getmeta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')
        resp.media = getmeta[1].__dict__
        resp.status = falcon.HTTP_200

    def on_post(self,req,resp,store_id,project_id,asset_id):
        try:
            meta = oveMeta()
            getmeta = fileStoreInterpret.getAssetMeta(store_id, project_id, asset_id, meta)
            if getmeta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
            # We input the old meta file, change the options, then re-write it to avoid deleting previous meta
            meta = getmeta[1]
            if is_empty(req.media.get('name')) is False:
                meta.setName(req.media.get('name'))
            if is_empty(req.media.get('description')) is False:
                meta.setDescription(req.media.get('description'))
            # There are issues checking whether a boolean is empty, since a False entry is the same as empty
            # if is_empty(bool(req.media.get('uploaded'))) is True:
            #     meta.isUploaded(bool(req.media.get('uploaded')))
            #     print(bool(req.media.get('uploaded')))
            setmeta = fileStoreInterpret.editAssetMeta(store_id,project_id,asset_id,meta)
            if setmeta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong - please check your meta is correct')
        resp.media = getmeta[1].__dict__
        resp.status = falcon.HTTP_200


app = falcon.API()

app.add_route('/api/listworkers',WorkersList())
app.add_route('/api/liststore', StoreList())
app.add_route('/api/{store_id}/list', ProjectList())
app.add_route('/api/{store_id}/{project_id}/list', AssetList())
app.add_route('/api/{store_id}/create', ProjectCreate())
app.add_route('/api/{store_id}/{project_id}/create',AssetCreate())
app.add_route('/api/{store_id}/{project_id}/{asset_id}/meta',MetaEdit())
app.add_route('/api/{store_id}/{project_id}/{asset_id}/upload',AssetUpload())
