package org.ove.am.proxy

import com.google.gson.Gson
import io.ktor.http.ContentType
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.io.File
import java.net.URI

private var logger: Logger = LoggerFactory.getLogger(ParameterSubstitution::class.java)

class ParameterSubstitution(propertiesPath: File, whitelistPath: File, private val storage: StorageBackend) {
    private val properties = loadVariables(propertiesPath)
    private val whitelist: WhitelistConfig = loadWhitelist(whitelistPath)

    fun shouldSubstitute(contentType: ContentType, resource: String): Boolean {
        if (whitelist.contentTypes.contains(contentType.toString()) || whitelist.contentTypes.contains(contentType.contentType)) {
            return true
        }

        if (whitelist.filenames.contains(resource.toLowerCase()) || whitelist.filenames.contains(File(resource).name.toLowerCase())) {
            return true
        }

        return false
    }

    fun replaceAll(text: String): String {
        var result = text
        properties.forEach { (key, value) ->
            result = result.replace("\${$key}", value)
        }
        result = dynamicReplaceLatest(result)
        return result
    }

    private fun dynamicReplaceLatest(text: String): String {
        var result = text
        var index = result.indexOf("\${LATEST}", startIndex = 0)
        while (index > 0) {
            val start = result.leftIndexOf('"', index) + 1
            val url = result.substring(start, index)
            if (url.startsWith("http")) {
                result = result.replaceFirst("\${LATEST}", getVersion(url))
            }
            index = result.indexOf("\${LATEST}", startIndex = index + 1)
        }
        return result
    }

    private fun getVersion(url: String): String {
        val version = storage.getResourceMeta(URI.create(url))["version"] ?: return ""

        return (version as Number).toInt().toString()
    }

    private fun loadVariables(file: File): Map<String, String> {
        val result = mutableMapOf<String, String>()
        if (file.exists()) {
            file.bufferedReader().use { reader ->
                reader.readLines().forEach { line ->
                    val tuple = line.split("=")
                    if (tuple.size == 2) {
                        result[tuple[0].trim().toUpperCase()] = tuple[1].trim()
                    }
                }
            }
        }
        logger.info("Loaded ${result.size} static variable substitution(s) ...")
        logger.info("1 dynamic variable substitution available ...")

        return result
    }

    private fun loadWhitelist(file: File): WhitelistConfig {
        val result = if (file.exists()) file.bufferedReader().use { Gson().fromJson(it, WhitelistConfig::class.java) } else WhitelistConfig()
        logger.info("Loaded ${result.filenames.size} whitelisted file(s) ...")
        logger.info("Loaded ${result.contentTypes.size} whitelisted content type(s) ...")
        return result
    }
}

fun String.leftIndexOf(char: Char, index: Int): Int {
    var idx = index
    while (idx >= 0 && this[idx] != char) {
        idx--
    }
    return idx
}