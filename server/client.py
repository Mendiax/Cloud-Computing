import argparse
from client_apps.client_oce import oce
from client_apps.client_one_of_n import one_of_n


protocols = {
    "oce": oce,
    "one_of_n" : one_of_n
}


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", dest="protocol",
                        choices=protocols.keys(), required=True)
    parser.add_argument("--u", dest="url", required=True)
    return parser.parse_args()





def main():
    arguments = parse_arg()
    protocols[arguments.protocol](arguments.url)


if __name__ == "__main__":
    main()
