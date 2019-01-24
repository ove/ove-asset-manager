from namedlist import namedlist

OveMeta = namedlist("OveMeta",
                    field_names=[("name", ""), ("description", ""), ("uploaded", False), ("permissions", "")],
                    default=None)
