from functools import reduce
from operator import mul as mul_func, add as add_func
from mcl import Fr


class Polynomial:
    """
    Polynomial of the form
    degree = n
    a_n*x^n + a_(n-1)*x^(n-1) + ... + a_1*x + a_0
    """

    def __init__(self, deg: int, seed):
        """
        We implicitly knows the degree of poly
        """
        self.coefficients = Polynomial._gen_coefficients(deg, seed)

    @staticmethod
    def _gen_coefficients(deg: int, seed) -> list:
        return [
            Fr.setHashOf(f'{seed}{i}'.encode())
            for i in range(deg + 1)
        ]

    def set_val_at_zero(self, val):
        self.coefficients[-1] = val

    def deg(self):
        return len(self.coefficients) - 1

    def __len__(self):
        return len(self.coefficients)

    def __call__(self, x):
        zero = Fr()
        zero.setInt(0)
        """
        Horner's schema:
        """
        return reduce(lambda acc, coef: acc * x + coef, self.coefficients, zero)

    def __getitem__(self, i):
        return self.coefficients[i]

    def __setitem__(self, i, value):
        self.coefficients[i] = value

    @staticmethod
    def lagrange_interpolation(x, phi):
        def term(i):
            xi, yi = phi[i]
            numerator = [(x - phi[j][0]) for j in range(len(phi)) if j != i]
            denominator = [(xi - phi[j][0]) for j in range(len(phi)) if j != i]
            return yi * (reduce(mul_func, numerator) / reduce(mul_func, denominator))

        return reduce(add_func, [term(i) for i in range(len(phi))])
