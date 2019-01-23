# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio

from minio import Minio
from minio.error import ResponseError
import io
import json
defaultStore = 'DODEVStore'


# Open a connection to the S3 storage
def openConnection(store):
    try:
        credentialsFile = 'credentials.conf'
        with open (credentialsFile) as f:
            storedetails = json.load(f)
        minioServer = storedetails['server']
        miniPort = storedetails['port']
        minioAccessKey = storedetails['access_key']
        minioSecretKey = storedetails['secret_key']

        minioServerCat = minioServer + ":" + miniPort
        minioClient = Minio(minioServerCat,
                            access_key=minioAccessKey,
                            secret_key=minioSecretKey,
                            secure=False)

        return minioClient

    except  Exception  as error:
        print(error)


# List the projects in an s3 storage (returning the names)
def listProjects():
    try:
        minioClient = openConnection(defaultStore)
        minioStoreBuckets = minioClient.list_buckets()
        minioBucketList = {}
        minioBucketList['Projects'] =[]
        for bucket in minioStoreBuckets:
            minioBucketList['Projects'].append(bucket.name)
        return minioBucketList

    except Exception as error:
        print(error)


# List the assets in an s3 bucket
def listAssets(projectName):
    try:
        minioClient = openConnection(defaultStore)
        minioProjectAssets = minioClient.list_objects(projectName, prefix=None, recursive=False)
        minioAssetList = {}
        minioAssetList['Assets'] =[]
        for asset in minioProjectAssets:
            # We define an asset in terms of a directory
            if asset.is_dir is True:
                dirToName = asset.object_name[0:-1]
                minioAssetList['Assets'].append(dirToName)
        return minioAssetList

    except Exception as error:
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


def createAsset(projectId,defmeta):
    try:
        minioClient = openConnection(defaultStore)
        # minio interprets the slash as a directory
        metaName = defmeta.name + '/' + '.ovemeta'
        # We create the meta file at the same time
        if getAssetMeta(projectId,defmeta.name,defmeta)[0] is True:
            return False, "This asset already exists"
        # We make a filestream and write it to the s3 storage
        print("Meta class working", defmeta.name)
        tempmeta = io.BytesIO(json.dumps(defmeta.__dict__).encode())
        filesize = tempmeta.getbuffer().nbytes
        print(minioClient.put_object(projectId,metaName,tempmeta,filesize))
        return True,"Asset created"
    except ResponseError as err:
        return False, err


def uploadAsset(projectId,assetName,filename,upfile):
    try:
        minioClient = openConnection(defaultStore)
        # filesize=os.stat(upfile.name).st_size
        filepath = assetName + '/' + filename
        print(minioClient.fput_object(projectId,filepath,upfile.name))
        return True, "Asset uploaded"
    except ResponseError as err:
        return False, err


def getAssetMeta(projectId,assetName,meta):
    try:
        minioClient = openConnection(defaultStore)
        metaName = assetName + '/' + '.ovemeta'
        print('Checking if asset exists')
        getmeta = minioClient.get_object(projectId,metaName)
        temp1 = io.BytesIO(getmeta.read())
        tempmeta = json.loads(temp1.read())
        meta.setName(tempmeta['name'])
        meta.setDescription(tempmeta['description'])
        meta.isUploaded(tempmeta['uploaded'])
        meta.setPermissions(tempmeta['permissions'])
        return True, meta
    except Exception as err:
        print("Check asset error is", err)
        return False, err


def setAssetMeta(projectId,assetName,meta):
    try:
        minioClient = openConnection(defaultStore)
        metaName = assetName + '/' + '.ovemeta'
        tempMeta = io.BytesIO(json.dumps(meta.__dict__).encode())
        filesize = tempMeta.getbuffer().nbytes
        print(minioClient.put_object(projectId, metaName,tempMeta,filesize))
        return True, tempMeta
    except Exception as err:
        print("Check asset error is", err)
        return False, err
