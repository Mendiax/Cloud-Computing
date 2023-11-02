import random
import mcl

from mcl import GT
from mcl import G2
from mcl import G1
from mcl import Fr

def get_fr(val : int):
    x = mcl.Fr()
    x.setInt(val)
    return x


# client
z = 8
secret_key = get_fr(123)

G = G1.hashAndMapTo(b"genQ")
PUBLIC_KEY = G * secret_key

# def PRNG(secret_key, file_ID, index):
#     random.seed(hash(secret_key.getStr()) + hash(file_ID) + hash(index))
#     random_value = mcl.Fr()
#     random_value.setInt(random.randint(0, 2**32))
#     return random_value

def create_polynomial(secret_key, file_ID):
    # polynomial = []
    # for i in range(0, z + 1):
    #     polynomial.append(PRNG(secret_key, file_ID, i))
    # return polynomial
    A = [
        mcl.Fr.setHashOf(f'{secret_key}{file_ID}{i}'.encode())
        for i in range(z + 1)]
    print(f'check {z+1}')
    return A
def print_polynomial(polynomial):
    for point in polynomial:
        print(f"a = {point.getStr()}")

def print_tagged_file(polynomial):
    for point in polynomial:
        print(f"m = {point[0].getStr()}, t = {point[1].getStr()}")

def fr_power(argument, exponent):
    value = mcl.Fr()
    value.setInt(1)
    for i in range(exponent):
        value = value * argument
    return value

def execute_polynomial_2(polynomial, argument):
    result = get_fr(0)
    for coefficient in polynomial:
        result = result * argument + coefficient
    return result


def execute_polynomial(polynomial, argument):
    return execute_polynomial_2(polynomial, argument)

def random_file():
    file = []
    for i in range(z + 1):
        file.append(random.randint(0, 2**32))
    return file

def read_file(path):
    file_l = []
    with open(path, 'rb') as file:
        byte = file.read(1)  # Read one byte at a time
        while byte:
            # Process the byte here (e.g., print it)
            print(byte, end=' ')
            # Read the next byte
            file_l.append(int.from_bytes(byte, byteorder='little'))
            byte = file.read(1)
    global z
    # print(f'check {z+1}')
    # print(file_l)
    z = len(file_l)
    return file_l



def tag_file(file, polynomial):
    tagged_file = []
    for i in range(len(file)):
        fr_file = get_fr(file[i])
        tagged_file.append((fr_file, execute_polynomial(polynomial, fr_file)))
    return tagged_file

def lagrange_interpolation(tagged_file, x):
    interpolation = mcl.G1()
    for point_1 in tagged_file:
        x_i, y_i = point_1
        multi = mcl.Fr()
        multi.setInt(1)
        for point_2 in tagged_file:
                x_j, y_j = point_2
                if x_i != x_j:
                    multi *= (x - x_j) / (x_i - x_j)
        multi = y_i * multi
        interpolation += multi
    return interpolation
file_name = "test_file.txt"
file = read_file(file_name)
file_ID = hash(file_name)

poly = create_polynomial(secret_key, file_name)
print(poly)
print('xd')
print(len(f'len poly:{len(poly)}'))
print(len(poly))
tagged_file = tag_file(file, poly)
print(f'{len(tagged_file)=}')
print(tagged_file)

# x_c = mcl.Fr()
# x_c.setByCSPRNG()
r = get_fr(12345)
x_c = get_fr(123456)

mcl_zero = mcl.Fr()
mcl_zero.setInt(0)
print(PUBLIC_KEY)
print('ex poly:')
print(execute_polynomial(poly, mcl_zero))
H = (PUBLIC_KEY, x_c, PUBLIC_KEY * (execute_polynomial(poly, mcl_zero)))
print('H:')
print(H)

PF = PUBLIC_KEY * execute_polynomial(poly, x_c)
# client end

#server
psi = []
psi.append((mcl_zero, H[2]))

for (m, t) in tagged_file:
    psi.append((m, PUBLIC_KEY * t))

RESPONSE = lagrange_interpolation(psi, x_c)
print(PF.getStr())
print(RESPONSE.getStr())
#server end

#client
print(PF == RESPONSE)
#client end