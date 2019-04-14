from wsgiref import simple_server

from workers.base import setup_worker


# do not use this in production
# this is a dev only method provided for convenience
def main():
    app = setup_worker(worker_class="workers.tulip.NetworkWorker", port=6092, worker_name="worker-tulip",
                       hostname="146.169.163.121", service_url="http://gdo-appsdev.dsi.ic.ac.uk:6080/api/workers")
    simple_server.make_server('0.0.0.0', 6092, app).serve_forever()  # nosec


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
