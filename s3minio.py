# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio

from minio import Minio
from minio.error import ResponseError
import os
import io

defaultStore = 'DODEVStore'


# Open a connection to the S3 storage
def openConnection(store):
    try:
        credentialsFile = 'credentials.conf'
        separator = ":"
        fileInput = open(credentialsFile, "r")
        fileLine = fileInput.readline()
        while fileLine:
            sout = fileLine.split(separator)
            minioServer = sout[0]
            miniPort = sout[1]
            minioAccessKey = sout[2]
            minioSecretKey = sout[3]
            fileLine = fileInput.readline()

        minioServerCat = minioServer + ":" + miniPort
        minioClient = Minio(minioServerCat,
                            access_key=minioAccessKey,
                            secret_key=minioSecretKey,
                            secure=False)

        return minioClient

    except (Exception) as error:
        print(error)


# List the projects in an s3 storage (returning the names)
def listProjects():
    try:
        minioClient = openConnection(defaultStore)
        minioStoreBuckets = minioClient.list_buckets()
        minioBucketList = []
        for bucket in minioStoreBuckets:
            minioBucketList.append(bucket.name)
        return minioBucketList

    except(Exception)as error:
        print(error)


# List the assets in an s3 bucket
def listAssets(projectName):
    try:
        minioClient = openConnection(defaultStore)
        minioProjectAssets = minioClient.list_objects(projectName, prefix=None, recursive=False)
        minioAssetList = []
        for asset in minioProjectAssets:
            # We define an asset in terms of a directory
            if asset.is_dir == True:
                dirToName = asset.object_name[0:-1]
                minioAssetList.append(dirToName)
        return minioAssetList

    except(Exception)as error:
        print(error)


def checkExists(projectName):
    try:
        minioClient = openConnection(defaultStore)
        doesExist = minioClient.bucket_exists(projectName)
        return doesExist
    except ResponseError as err:
        return False


def createProject(projectName):
    try:
        minioClient = openConnection(defaultStore)
        makeProject = minioClient.make_bucket(projectName, location='us-east-1')
    except ResponseError as err:
        return False



def createAsset(projectId,assetName):
    try:
        minioClient = openConnection(defaultStore)
        #minio interprets the slash as a directory
        assetaddslash = assetName + '/'
        metaName = assetaddslash + 'ovemeta'
        with open('ove-meta','rb') as file_data:
            file_stat = os.stat('ove-meta')
            print(minioClient.put_object(projectId,metaName,file_data,file_stat.st_size))
    except ResponseError as err:
        return False

