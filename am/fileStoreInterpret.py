# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations

from am import s3minio

defaultStore = 'DODEVStore'
assetDescription = 'Place holder for description field'
# by default we treat everything as s3 storage. This can be extended to filestore, swift etc.
storeType = 's3'

# We define the default meta data structure
defmeta = {}
defmeta['Name'] = ''
defmeta['Description'] = ''
defmeta['Uploaded'] = False


# List the projects in an storage (returning the names)
def listProjects(storeId):
    try:
        if storeType == 's3':

            projectList = s3minio.listProjects()
        return projectList
    except Exception as error:
        print(error)


def listAssets(storeId,projectId):
    try:
        if storeType == 's3':
            assetList = s3minio.listAssets(projectId)
        return assetList
    except Exception as error:
        print(error)

# List the assets in an s3 bucket
def listAllAssets(storeId, projectId):
    try:
        if storeType == 's3':
            assetList = s3minio.listAssets(projectId)
        return assetList

    except Exception as error:
        print(error)


def showMeta(storeId, projectId, assetId):
    try:
        if storeType == 's3':
            metaData = True;
        return metaData
    except Exception as error:
        print(error)


def createProject(storeId, newProject):
    try:
        if storeType == 's3':
            if s3minio.checkExists(newProject) == True:
                return False, "This project name already exists"
            else:
                s3minio.createProject(newProject)
        return True, "Successfully created new project"
    except Exception as error:
        print(error)
        return False, str(error)


def createAsset(storeId,projectId,meta):
    try:
        # defmeta['Name'] = newAsset
        # defmeta['Description'] = assetDescription
        if storeType == 's3':
            result = s3minio.createAsset(projectId, meta)
            if result[0] is True:
                return True, result[1]
            else:
                return False, result[1]
    except Exception as error:
        print(error)
        return False, str(error)

def uploadAsset(storeId,projectId,assetName,filename,meta,file):
    try:
        if storeType == 's3':
            result = s3minio.uploadAsset(projectId, assetName, filename, file)
            print("Setting uploaded flag to True")
            meta.isUploaded(True)
            s3minio.setAssetMeta(projectId, assetName, meta)
            if result[0] is True:
                return True, result[1]
            else:
                return False, result[1]
    except Exception as error:
        print(error)
        return False, str(error)


def getAssetMeta(storeId,projectId,assetName,meta):
    try:
        if storeType =='s3':
            result = s3minio.getAssetMeta(projectId, assetName, meta)
            if result[0] is True:
                return True, result[1]
            else:
                print(result[1])
                return False, result[1]
    except Exception as error:
        print(error)
        return False, error

def editAssetMeta(storeId,projectId,assetName,meta):
    try:
        if storeType =='s3':
            result = s3minio.setAssetMeta(projectId, assetName, meta)
            if result[0] is True:
                return True, result[0]
            else:
                print(result[1])
                return False, result[1]
    except Exception as error:
        print(error)
        return False,str(error)
