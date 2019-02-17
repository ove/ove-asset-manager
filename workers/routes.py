import falcon

from workers import FileController


class WorkerRoute:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_head(self, _: falcon.Request, resp: falcon.Response):
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        # resp.media = worker.to_public_json()
        resp.status = falcon.HTTP_200
