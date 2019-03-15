from wsgiref import simple_server

from workers.base import setup_worker


# do not use this in production
# this is a dev only method provided for convenience
def main():
    app = setup_worker(worker_class="workers.dzi.DeepZoomImageWorker", port=6091, worker_name="worker-dzi")
    simple_server.make_server('0.0.0.0', 6091, app).serve_forever()  # nosec


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
