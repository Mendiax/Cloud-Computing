import unittest

from mcl import Fr

MAX_LEN = 400
def set_xor_max_len(val : int):
    global MAX_LEN
    MAX_LEN = val

def xor_strings(str1, str2):
    """
    Performs an XOR operation on two strings.

    @param str1: The first string.
    @param str2: The second string.
    @return: A new string resulting from the XOR operation of the two input strings.

    Example:
        >>> xor_strings("hello", "world")
        '\x1f\x0f\x0e\x0e\x04'
    """
    # print(str1)
    # print(str2)

    assert len(str1) <= MAX_LEN, f'{MAX_LEN=} {len(str1)=} {str1}'
    assert len(str2) <= MAX_LEN, f'{MAX_LEN=} {len(str2)=} {str2}'

    str1_aligned = str1.ljust(MAX_LEN, "\x00")
    str2_aligned = str2.ljust(MAX_LEN, "\x00")
    return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(str1_aligned, str2_aligned))

def remove_trailing_zeros(input_string):
    """
    Removes trailing '\x00' characters from a string.

    @param input_string: The string from which to remove trailing '\x00' characters.
    @return: A new string with trailing '\x00' characters removed.

    Example:
        >>> remove_trailing_zeros("hello\x00\x00\x00")
        'hello'
    """
    return input_string.rstrip('\x00')

def encrypt(m : str, k):
    return xor_strings(m, k.getStr().decode())

def decrypt(c : str, k):
    return remove_trailing_zeros(xor_strings(c, k.getStr().decode()))

def get_ith_bit(j: int, i: int) -> int:
    """
    Get the i-th bit of an l-bit integer j.

    :param j: The integer from which to extract the bit.
    :type j: int
    :param i: The position of the bit to extract (0-based index).
    :type i: int
    :return: The i-th bit of j.
    :rtype: int
    """
    if i < 0:
        raise ValueError("Index i must be non-negative")

    # Right shift j by i, then check the LSB
    return (j >> i) & 1


class TestXorStrings(unittest.TestCase):
    # def test_normal_case(self):
    #     """ Test normal case with two strings. """
    #     self.assertEqual(xor_strings("hello", "world"), '\x1f\x0f\x0e\x0e\x04')

    def test_empty_strings(self):
        """ Test with two empty strings. """
        self.assertEqual(xor_strings("", ""), "\x00" * MAX_LEN)

    def test_one_empty_string(self):
        """ Test with one empty string and one non-empty string. """
        self.assertEqual(xor_strings("", "hello"), "hello".ljust(MAX_LEN, "\x00"))
        self.assertEqual(xor_strings("world", ""), "world".ljust(MAX_LEN, "\x00"))

    def test_same_strings(self):
        """ Test with two identical strings. """
        self.assertEqual(xor_strings("hello", "hello"), "\x00" * MAX_LEN)

    def test_aba(self):
        """ Test with two identical strings. """
        x1 = xor_strings("hello", "world")
        x2 = xor_strings(x1, "hello")
        self.assertEqual(x2, "world".ljust(MAX_LEN, "\x00"))

    # def test_different_lengths(self):
    #     """ Test with strings of different lengths. """
    #     self.assertEqual(xor_strings("short", "a longer string"), "\x13\x12\x06\x17\x07")

    # def test_non_ascii(self):
    #     """ Test with non-ASCII characters. """
    #     self.assertEqual(xor_strings("héllo", "wørld"), '\x1f\x0b\x1e\x1a\x04')

if __name__ == '__main__':
    unittest.main()
