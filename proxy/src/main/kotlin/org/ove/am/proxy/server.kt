package org.ove.am.proxy


import io.ktor.application.call
import io.ktor.application.install
import io.ktor.features.*
import io.ktor.http.CacheControl
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.content.CachingOptions
import io.ktor.http.content.OutgoingContent
import io.ktor.response.header
import io.ktor.response.lastModified
import io.ktor.response.respond
import io.ktor.response.respondText
import io.ktor.routing.get
import io.ktor.routing.routing
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.utils.io.ByteWriteChannel
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.net.URLEncoder

private var logger: Logger = LoggerFactory.getLogger("Server")

private val cacheOptions = CachingOptions(CacheControl.NoStore(CacheControl.Visibility.Private))

fun setupServer(port: Int, storage: StorageBackend, substitution: ParameterSubstitution) {
    val server = embeddedServer(Netty, configure = {
        requestQueueLimit = 128
        requestReadTimeoutSeconds = 5 * 60 // 5 minutes
        responseWriteTimeoutSeconds = 5 * 60 // 5 minutes
    }, port = port, watchPaths = emptyList()) {
        install(DefaultHeaders)
        install(Compression)
        install(CallLogging)
        install(CORS) { anyHost() }

        install(CachingHeaders) {
            options { outgoingContent ->
                when (outgoingContent.contentType?.withoutParameters()) {
                    ContentType.Application.Json -> cacheOptions
                    ContentType.Text.Xml -> cacheOptions
                    ContentType.Application.Xml -> cacheOptions
                    ContentType.Text.Html -> cacheOptions
                    else -> null
                }
            }
        }

        install(StatusPages) {
            exception<AccessDeniedError> { call.respond(HttpStatusCode.Forbidden) }
            exception<ResourceNotFoundError> { call.respond(HttpStatusCode.NotFound) }
            exception<InvalidRequestError> { call.respond(HttpStatusCode.BadRequest) }
            exception<Throwable> {
                logger.error("Exception in service call. $it")
                call.respondText(
                        contentType = ContentType.Text.Any,
                        status = HttpStatusCode.InternalServerError,
                        text = "Service error"
                )
            }
        }

        install(PartialContent) { maxRangeCount = 10 }

        routing {
            get("/{store}/{project}/{resource...}") {
                val resource = try {
                    storage.getResourceData(
                            store = call.parameters["store"],
                            project = call.parameters["project"],
                            resource = call.parameters.getAll("resource")?.joinToString("/")
                    )
                } catch (e: ResourceNotFoundError) {
                    storage.getResourceData(
                            store = call.parameters["store"],
                            project = call.parameters["project"],
                            resource = call.parameters.getAll("resource")?.joinToString("/") { URLEncoder.encode(it, "utf-8") }
                    )
                }

                call.response.lastModified(resource.modifiedDate)
                call.response.header("Accept-Ranges", "bytes")

                val contentType = ContentType.parse(resource.contentType)

                if (substitution.shouldSubstitute(contentType, resource.resource)) {
                    resource.input.bufferedReader()
                            .use { call.respondText(substitution.replaceAll(it.readText()), contentType) }
                } else {
                    call.respond(object : OutgoingContent.WriteChannelContent() {
                        override val contentType = contentType
                        override val contentLength = resource.length
                        override suspend fun writeTo(channel: ByteWriteChannel) {
                            resource.input.use { streamResource(resource.name, it, channel) }
                        }
                    })
                }
            }
        }
    }
    server.start(wait = false)
}
