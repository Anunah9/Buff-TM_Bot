import logging


def main():
    try:
        print(ffff)
    except Exception as ex:
        print(ex)
        logging.error(msg=ex)


if __name__ == "__main__":
    logging.basicConfig(
        filename="mylog.log",
        format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
    )

    main()

