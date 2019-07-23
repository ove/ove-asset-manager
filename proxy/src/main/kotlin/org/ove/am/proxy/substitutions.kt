package org.ove.am.proxy

import java.io.File
import java.net.URI

class ParameterSubstitution(propertiesPath: File, private val storage: StorageBackend) {
    private val properties = mutableMapOf<String, String>()

    init {
        if (propertiesPath.exists()) {
            propertiesPath.bufferedReader().use { reader ->
                reader.readLines().forEach { line ->
                    val tuple = line.split("=")
                    properties[tuple[0].trim().toUpperCase()] = tuple[1].trim()
                }
            }
        }
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
}

fun String.leftIndexOf(char: Char, index: Int): Int {
    var idx = index
    while (idx >= 0 && this[idx] != char) {
        idx--
    }
    return idx
}