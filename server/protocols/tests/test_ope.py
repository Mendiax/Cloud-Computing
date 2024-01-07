from protocols.protocol_ope import OpeCloud, OpeUser
from mcl import Fr


def test_ope():
    zero = Fr()
    zero.setInt(0)
    opeCloud = OpeCloud()
    alpha = Fr()
    alpha.setInt(10)
    assert opeCloud.poly_x(zero) == zero
    opeUser = OpeUser(alpha)
    expected_val = opeCloud.poly_p(alpha)
    tags = opeUser.generate_xy()
    assert opeUser.poly_s(zero) == alpha
    poly_q_values = opeCloud.generate_values_of_poly_q(tags)
    real_val = opeUser.calculate_poly_r(poly_q_values)
    assert expected_val == real_val
