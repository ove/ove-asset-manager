# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations

import s3minio

defaultStore = 'DODEVStore'
# by default we treat everything as s3 storage. This can be extended to filestore, swift etc.
storeType = 's3'


# List the projects in an storage (returning the names)
def listProjects(storeId):
    try:
        if storeType == 's3':
            projectList = s3minio.listProjects()
        return projectList
    except(Exception)as error:
        print(error)


# List the assets in an s3 bucket
def listAssets(storeId, projectId):
    try:
        if storeType == 's3':
            assetList = s3minio.listAssets(projectId)
        return assetList

    except(Exception)as error:
        print(error)


def showMeta(storeId, projectId, assetId):
    try:
        if storeType == 's3':
            metaData = True;
        return metaData
    except(Exception)as error:
        print(error)


def createProject(storeId, newProject):
    try:
        if storeType == 's3':
            if s3minio.checkExists(newProject) == True:
                return False, "This project name already exists"
            else:
                s3minio.createProject(newProject)
        return True, "Successfully created new project"
    except(Exception)as error:
        print(error)
        return False, str(error)

def createAsset(storeId,projectId,newAsset):
    try:
        if storeType =='s3':
            s3minio.createAsset(projectId,newAsset)
            return True, "Asset created"
    except(Exception)as error:
        print(error)
        return False, str(error)