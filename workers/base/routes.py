import falcon

from workers.base.worker import BaseWorker


class WorkerStatusRoute:
    def __init__(self, worker: BaseWorker):
        self._worker = worker

    def on_head(self, _: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200 if self._worker is not None else falcon.HTTP_500

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.media = {'status': str(self._worker.status)}
        resp.status = falcon.HTTP_200

    def on_post(self, _: falcon.Request, resp: falcon.Response):
        status = self._worker.reset_status()

        resp.media = {'Status': str(status)}
        resp.status = falcon.HTTP_200
