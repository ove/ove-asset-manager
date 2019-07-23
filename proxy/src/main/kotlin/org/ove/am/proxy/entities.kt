package org.ove.am.proxy

import java.io.InputStream
import java.time.ZonedDateTime

class ResourceNotFoundError : Exception()
class AccessDeniedError : Exception()


data class StoreCredentials(
    val name: String = "",
    val endpoint: String = "",
    val proxyUrl: String = "",
    val accessKey: String = "",
    val secretKey: String = ""
)

data class StoreConfig(val default: String = "", val stores: List<StoreCredentials> = emptyList())

data class ResourceData(
    val name: String,
    val contentType: String,
    val etag: String,
    val modifiedDate: ZonedDateTime,
    val length: Long,
    val input: InputStream
)