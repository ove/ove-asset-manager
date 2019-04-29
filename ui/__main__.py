from wsgiref import simple_server

from ui import setup_ui


# do not use this in production
# this is a dev only method provided for convenience
def main():
    simple_server.make_server('0.0.0.0', 6060, setup_ui(backend_url="http://localhost:6080/")).serve_forever()  # nosec


if __name__ == "__main__":
    main()
