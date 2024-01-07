from mcl import *
from .protocols_utils import *
from .polynomial import Polynomial
from secrets import SystemRandom
from operator import itemgetter

# sec params
SEED_CLOUD_1 = "TEST1"
SEED_CLOUD_2 = "TEST2"
SEED_USER = "TEST3"
DEG_POLY_P = 10
SEC_PARAM_M = 5
SEC_PARAM_K = 5
SEC_PARAM_N = SEC_PARAM_K * DEG_POLY_P + 1
SEC_PARAM_BIG_N = SEC_PARAM_N * SEC_PARAM_M


class OpeCloud:
    def __init__(self) -> None:
        self.poly_p = Polynomial(DEG_POLY_P, SEED_CLOUD_1)
        _poly_x_deg = SEC_PARAM_K * DEG_POLY_P
        self.poly_x = Polynomial(_poly_x_deg, SEED_CLOUD_2)
        poly_x_val_at_zero = Fr()
        poly_x_val_at_zero.setInt(0)
        self.poly_x.set_val_at_zero(poly_x_val_at_zero)

    def _calc_q(self, x, y):
        return self.poly_x(x) + self.poly_p(y)

    def generate_values_of_poly_q(self, tags: list[tuple[Fr, Fr]]):
        poly_q_values = []
        for x_val, y_val in tags:
            q_xy = self._calc_q(x_val, y_val)
            poly_q_values.append(q_xy)

        return poly_q_values


class OpeUser:
    def __init__(self, alpha: Fr) -> None:
        self.alpha = alpha
        self.subset_of_n_indices = []
        self.random_gen = SystemRandom()

    def generate_xy(self):
        self.list_of_all_xs = [
            Fr.rnd()
            for _ in range(SEC_PARAM_BIG_N)
        ]
        self.poly_s = Polynomial(SEC_PARAM_K, seed=SEED_USER)
        self.poly_s.set_val_at_zero(self.alpha)

        self.subset_of_n_indices = self.random_gen.sample(
            range(SEC_PARAM_BIG_N), SEC_PARAM_N)

        tags = [
            (x, self.poly_s(x)) if i in self.subset_of_n_indices else
            (x, Fr.rnd())
            for i, x in enumerate(self.list_of_all_xs)
        ]

        return tags

    def calculate_poly_r(self, poly_q_values):
        list_of_proper_xs = list(itemgetter(
            *self.subset_of_n_indices)(self.list_of_all_xs))
        list_of_proper_poly_q_values = list(
            itemgetter(*self.subset_of_n_indices)(poly_q_values))
        pairs_of_poly_q = [_ for _ in zip(
            list_of_proper_xs, list_of_proper_poly_q_values)]
        zero = Fr()
        zero.setInt(0)
        return Polynomial.lagrange_interpolation(zero, pairs_of_poly_q)
