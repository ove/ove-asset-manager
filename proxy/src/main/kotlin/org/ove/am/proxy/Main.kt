package org.ove.am.proxy


import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.io.File


private var logger: Logger = LoggerFactory.getLogger("Main")

fun main(argv: Array<String>) = StartServerCommand().main(argv)

class StartServerCommand : CliktCommand(name = "server") {
    private val port: Int by option(
            "--port",
            help = "Server port (default: $defaultPort)"
    ).int().default(defaultPort)

    private val configFile: String by option(
            "--config",
            help = "Config file (default: $defaultConfigFile)"
    ).default(defaultConfigFile)

    private val environmentFile: String by option(
            "--environment",
            help = "Environment file (default: $defaultEnvironmentFile)"
    ).default(defaultEnvironmentFile)

    private val whitelistFile: String by option(
            "--whitelist",
            help = "Whitelist file (default: $defaultWhitelistFile)"
    ).default(defaultWhitelistFile)

    override fun run() {
        logger.info("[CmdLine] Port: $port")

        val storage = StorageBackend(configFile)
        val substitution = ParameterSubstitution(propertiesPath = File(environmentFile), whitelistPath = File(whitelistFile), storage = storage)
        setupServer(port = port, storage = storage, substitution = substitution)
    }
}

const val defaultPort = 6081
const val defaultConfigFile = "config/credentials.json"
const val defaultEnvironmentFile = "config/environment.properties"
const val defaultWhitelistFile = "config/whitelist.json"