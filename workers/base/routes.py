import falcon

from common.entities import WorkerStatus
from common.errors import ValidationError
from common.validation import validate_not_null
from workers.base.worker import process_request, BaseWorker


class WorkerRoute:
    def __init__(self, worker: BaseWorker):
        self._worker = worker

    def on_head(self, _: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200 if self._worker is not None else falcon.HTTP_500

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        if self._worker is None or type(self._worker) == BaseWorker:
            raise ValidationError(title="Worker not configured", description="Please configure the worker first")

        if self._worker.status is not WorkerStatus.READY:
            raise ValidationError(title="Worker not ready", description="This worker is doing something useful. Please check the status.")

        validate_not_null(req.media, 'store_config')
        validate_not_null(req.media, 'project_name')
        validate_not_null(req.media, 'asset_name')

        process_request(store_config=req.media.get("store_config"), project_name=req.media.get("project_name"),
                        asset_name=req.media.get("asset_name"), worker=self._worker, task_options=req.media.get("task_options", dict()))

        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class WorkerStatusRoute:
    def __init__(self, worker: BaseWorker):
        self._worker = worker

    def on_head(self, _: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200 if self._worker is not None else falcon.HTTP_500

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.media = {'Status': str(self._worker.status)}
        resp.status = falcon.HTTP_200

    def on_post(self, _: falcon.Request, resp: falcon.Response):
        status = self._worker.reset_status()

        resp.media = {'Status': str(status)}
        resp.status = falcon.HTTP_200
