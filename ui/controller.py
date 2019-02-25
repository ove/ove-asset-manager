from typing import Dict, List, Any

from ui.backend import BackendClient

_RESERVED_NAMES = {"list", "validate", "create"}


class BackendController:
    def __init__(self, backend_url: str):
        self._backend = BackendClient(backend_url=backend_url)

    def list_workers(self) -> List:
        return self._backend.get("api/workers") or []

    def edit_worker(self, action: str, name: str) -> None:
        if action == "reset":
            self._backend.post("api/workers/status", data={"name": name})
        elif action == "delete":
            self._backend.delete("api/workers", data={"name": name})

    def list_stores(self) -> List:
        return self._backend.get("api/list") or []

    def list_projects(self, store_name: str) -> List:
        projects = self._backend.get("api/{}/list".format(store_name)).get("Projects", [])
        projects_with_project = set(self._backend.get("api/{}/list?hasObject=project".format(store_name)).get("Projects", []))
        return [{"name": project, "has_project": project in projects_with_project} for project in projects]

    def create_project(self, store_name: str, project_name: str) -> None:
        self._backend.post("api/{}/create".format(store_name), data={"name": project_name})

    def list_assets(self, store_name: str, project_name: str) -> List:
        assets = self._backend.get("api/{}/{}/list".format(store_name, project_name)).get("Assets", {})
        return [v for v in assets.values()]

    def get_asset(self, store_name: str, project_name: str, asset_name: str) -> Dict:
        return self._backend.get("api/{}/{}/meta/{}".format(store_name, project_name, asset_name))

    def create_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        self._backend.post("api/{}/{}/create".format(store_name, project_name), data=asset)
        return self.get_asset(store_name=store_name, project_name=project_name, asset_name=asset.get("name", ""))

    def edit_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        return self._backend.post("/api/{}/{}/meta/{}".format(store_name, project_name, asset.get("name", "")), data=asset)

    def upload_asset(self, store_name: str, project_name: str, asset_name: str, filename: str, stream: Any) -> None:
        url = "api/{}/{}/createUpload/{}".format(store_name, project_name, asset_name)
        headers = {"Content-Type": "application/octet-stream", "content-disposition": "filename='{}'".format(filename)}
        self._backend.upload(api_url=url, stream=stream, headers=headers)

    # def get_object(self, project_name: str, object_name: str, store_name: str = None) -> Union[None, Dict]:
    #     return self._manager.get_object(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    # def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None, update: bool = False) -> None:
    #     if not update and self._manager.has_object(store_name=store_name, project_name=project_name, object_name=object_name):
    #         raise ObjectExistsError(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    #     return self._manager.set_object(store_name=store_name, project_name=project_name, object_name=object_name, object_data=object_data)
