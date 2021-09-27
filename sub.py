from rns import *
from setup import rand_rns

crt_modulus_bit_len = 32

# running this to hit some adjusted aux cases
for offset in range(1, crt_modulus_bit_len // 8 + 1):
    for i in range(1000):
        _ = rand_rns(crt_modulus_bit_len, offset)

u0_bit_len = {}
u1_bit_len = {}

for offset in range(1, crt_modulus_bit_len // 8 + 1):
    for i in range(1000):

        rns = rand_rns(crt_modulus_bit_len, offset)
        p = rns.wrong_modulus

        a = rns.max()
        b = rns.zero()
        r, q, t, u0, u1 = a - b
        assert r.value() == (a.value() - b.value()) % p
        assert q

        a = rns.zero()
        b = rns.max()
        r, q, t, u0, u1 = a - b
        assert r.value() == (a.value() - b.value()) % p

        a = rns.rand_in_max()
        b = rns.rand_in_max()
        r, q, t, u0, u1 = a - b
        assert r.value() == (a.value() - b.value()) % p

        _u0 = u0.bit_length()
        _u1 = u1.bit_length()

        if _u0 not in u0_bit_len:
            u0_bit_len[_u0] = 0

        if _u1 not in u1_bit_len:
            u1_bit_len[_u1] = 0

        u0_bit_len[_u0] += 1
        u1_bit_len[_u1] += 1

    print("offset", offset)
    print("--- u0 bit")
    for key in u0_bit_len.keys():
        print(key, u0_bit_len[key])

    print("--- u1 bit")
    for key in u1_bit_len.keys():
        print(key, u1_bit_len[key])
    print("")
