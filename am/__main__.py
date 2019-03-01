from wsgiref import simple_server

from am import setup_app


# do not use this in production
# this is a dev only method provided for convenience
def main():
    simple_server.make_server('0.0.0.0', 6080, setup_app()).serve_forever()  # nosec


if __name__ == "__main__":
    main()
