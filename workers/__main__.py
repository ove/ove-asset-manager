from wsgiref import simple_server

from workers import setup_worker


# do not use this in production
# this is a dev only method provided for convenience
def main():
    simple_server.make_server('0.0.0.0', 9080, setup_worker()).serve_forever()  # nosec


if __name__ == "__main__":
    main()
