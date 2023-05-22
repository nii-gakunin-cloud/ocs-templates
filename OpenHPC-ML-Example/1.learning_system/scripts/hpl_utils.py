import math
import sys


def hpl_pq(num):
    num_sr = int(math.sqrt(num))
    dv = [(x, num // x) for x in range(1, num_sr + 1) if num % x == 0]
    return min(dv, key=lambda x: x[1] - x[0] if x[0] != x[1] else sys.maxsize)
