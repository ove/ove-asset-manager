package org.ove.am.proxy

import com.google.gson.Gson
import io.minio.MinioClient
import kotlinx.coroutines.io.ByteWriteChannel
import kotlinx.coroutines.io.close
import okhttp3.HttpUrl
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.io.File
import java.io.FileReader
import java.io.InputStream
import java.net.URI
import java.time.ZoneId
import java.time.ZonedDateTime

private var logger: Logger = LoggerFactory.getLogger(StorageBackend::class.java)

private const val BUFFER_SIZE = 1024

class StorageBackend(configFile: String) {
    private val gson = Gson()
    private val clients = setup(configFile)

    private fun setup(configFile: String): Map<String, MinioClient> {
        val config = if (File(configFile).exists())
            FileReader(configFile).use {
                gson.fromJson(it, StoreConfig::class.java)
            }.stores.map { Pair(it.name, MinioClient(parseUrl(it.endpoint), it.accessKey, it.secretKey)) }.toMap()
        else emptyMap()

        logger.info("Loaded ${config.size} store(s) ...")
        return config
    }

    private fun parseUrl(endpoint: String) =
            if (endpoint.startsWith("http://") || endpoint.startsWith("https://"))
                HttpUrl.parse(endpoint)
            else HttpUrl.parse("http://$endpoint")


    private fun client(store: String) = clients.getOrElse(store) {
        logger.error("Store not found: $store")
        throw ResourceNotFoundError()
    }

    fun getResourceData(store: String?, project: String?, resource: String?): ResourceData {
        if (store.isNullOrBlank() || project.isNullOrBlank() || resource.isNullOrBlank()) {
            throw ResourceNotFoundError()
        }

        if (resource.endsWith(".ovemeta")) {
            throw AccessDeniedError()
        }

        val client = client(store)

        if (!client.bucketExists(project)) {
            logger.error("Project not found: $project")
            throw ResourceNotFoundError()
        }

        try {
            val stat = client.statObject(project, resource)
            return ResourceData(
                    name = stat.name(),
                    resource = resource,
                    contentType = probeContentType(resource),
                    etag = stat.etag(),
                    modifiedDate = ZonedDateTime.ofInstant(stat.createdTime().toInstant(), ZoneId.systemDefault()),
                    length = stat.length(),
                    input = client.getObject(project, resource)
            )
        } catch (e: Throwable) {
            logger.error("Error while getting object. $e")
            throw ResourceNotFoundError()
        }
    }

    // internal use only
    fun getResourceMeta(url: URI): Map<*, *> {
        if (url.path.isNullOrEmpty()) {
            throw ResourceNotFoundError()
        }

        val parts = url.path.split("/", limit = 4)
        if (parts.size != 4) {
            throw ResourceNotFoundError()
        }

        val store = parts[1]
        val project = parts[2]
        val resource = parts[3]

        if (store.isBlank() || project.isBlank() || resource.isBlank()) {
            throw ResourceNotFoundError()
        }

        val client = client(store)

        if (!client.bucketExists(project)) {
            logger.error("Project not found: $project")
            throw ResourceNotFoundError()
        }

        try {
            return client.getObject(project, appendSlash(resource) + ".ovemeta").reader().use {
                gson.fromJson(it, Map::class.java)
            }
        } catch (e: Throwable) {
            logger.error("Error while getting object meta. $e")
            throw ResourceNotFoundError()
        }
    }
}

suspend fun streamResource(name: String, input: InputStream, output: ByteWriteChannel) {
    var running = true
    while (running) {
        val buffer = input.readNBytes(BUFFER_SIZE)
        try {
            if (buffer.isNotEmpty()) {
                output.writeFully(buffer, 0, buffer.size)
            } else {
                running = false
            }
        } catch (e: Throwable) {
            running = false
            logger.error("Error while streaming resource: $name")
        }
    }
    output.flush()
    output.close()
}