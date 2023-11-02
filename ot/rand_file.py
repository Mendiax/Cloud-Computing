

import random


def random_file(no_bytes : int):
    name = f'random_file_{no_bytes}b.txt'
    with open(name, 'w') as fd:
        for i in range(no_bytes//2):
            fd.write(random.randint(0, 15).to_bytes(1, 'big').hex())




if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        random_file(int(sys.argv[1]))