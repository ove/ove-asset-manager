class OveMeta:
    def __init__(self, name: str = "", description: str = "", uploaded: bool = False, permissions: str = ""):
        self.name = name
        self.description = description
        self.uploaded = uploaded
        self.permissions = permissions


class ApiResult:
    def __init__(self, success: bool = True, data=None, message: str = None, status: str = "200"):
        self.success = success
        self.data = data
        self.message = message
        self.status = status
