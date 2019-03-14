# Tulip Network Layout Worker

This worker uses the [Tulip visualization framework](http://tulip.labri.fr/TulipDrupal/) to apply Network layout algorithms to networks.

Documentation for the layout algorithms is [available here](http://tulip.labri.fr/Documentation/current/tulip-python/html/tulippluginsdocumentation.html#layoutpluginsdoc).

Tulip will select an export function based on the extension of the provided output filename.
[The supported formats are](http://tulip.labri.fr/Documentation/current/tulip-python/html/tulipreference.html?highlight=savegraph#tulip.tlp.saveGraph): TLP (.tlp, .tlp.gz, .tlpz), TLP Binary (.tlpb, .tlpb.gz, .tlpbz), TLP JSON (.json), GML (.gml), CSV (.csv). Note that SVG is not available, as this depends on the QT GUI for Tulip.