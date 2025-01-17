class Integer:

    def __init__(self, rns, limbs):
        self.rns = rns
        self.limbs = limbs

    def __mul__(self, other):

        self_val = self.value()
        other_val = other.value()
        p_val = self.wrong_modulus()

        q_val = (self_val * other_val) // p_val
        r_val = (self_val * other_val) % p_val

        N = self.rns.number_of_limbs
        p = self.rns.neg_wrong_modulus_limbs()
        q = self.rns.value_to_limbs(q_val, N + 1)
        r = self.rns.value_to_limbs(r_val)
        n = self.rns.native_modulus

        # print("q4", q[number_of_limbs].bit_length())

        t = [0] * (2 * N - 1)
        for i in range(N):
            for j in range(N):
                t[i + j] = (t[i + j] + self[i] * other[j] + p[i] * q[j]) % n

        v0, v1 = self.residues(t, r)

        _q = self.rns.from_limbs(q)
        _r = self.rns.from_limbs(r)

        must_be_zero = self.value() * other.value()
        must_be_zero = must_be_zero - p_val * _q.value()
        must_be_zero = must_be_zero - _r.value()
        assert must_be_zero % n == 0

        return Integer(self.rns, r), q, t, v0, v1

    def bad_mul_2(self, other):

        T = self.rns.T
        p_val = self.wrong_modulus()
        n = self.rns.native_modulus
        q_val = n * T // p_val
        r_val = n * T % p_val

        print("T ", hex(T))
        print("n ", hex(n))
        print("q ", hex(q_val), "expect true:", q_val < T)
        print("r ", hex(r_val), "expect true:", r_val < p_val)
        print("nT", hex(n * T))

        N = self.rns.number_of_limbs
        p = self.rns.neg_wrong_modulus_limbs()
        q = self.rns.value_to_limbs(q_val, N + 1)
        r = self.rns.value_to_limbs(r_val)

        n = self.rns.native_modulus

        t = [0] * (2 * N - 1)
        for i in range(N):
            for j in range(N):
                t[i + j] = (t[i + j] + self[i] * other[j] + p[i] * q[j]) % n

        v0, v1 = self.residues(t, r)

        _q = self.rns.from_limbs(q)
        _r = self.rns.from_limbs(r)

        must_be_zero = self.value() * other.value()
        must_be_zero = must_be_zero - p_val * _q.value()
        must_be_zero = must_be_zero - _r.value()
        assert must_be_zero % n == 0

        return Integer(self.rns, r), q, t, v0, v1

    def bad_mul(self, other):

        self_val = self.value()
        other_val = other.value()
        p_val = self.wrong_modulus()

        T = self.rns.T
        q_T_val = T // p_val
        r_T_val = T % p_val

        q_val = (self_val * other_val) // p_val
        r_val = (self_val * other_val) % p_val
        print("q", hex(q_val), hex(q_T_val), q_val < p_val)
        print("r", hex(r_val), hex(r_T_val), r_val < p_val)

        q_fixed = q_val - q_T_val
        r_fixed = r_val - r_T_val
        if r_fixed < 0:
            r_fixed = r_fixed + p_val
            q_fixed = q_fixed - 1

        print("q_f", hex(q_fixed))
        print("r_f", hex(r_fixed))

        print("expect true", q_val * p_val + r_val == self_val * other_val)
        print("expect false", q_fixed * p_val + r_fixed == self_val * other_val)
        print("diff", hex((q_val * p_val + r_val) - (q_fixed * p_val + r_fixed)))

        q_val = q_fixed
        r_val = r_fixed

        N = self.rns.number_of_limbs
        p = self.rns.neg_wrong_modulus_limbs()
        q = self.rns.value_to_limbs(q_val, N + 1)
        r = self.rns.value_to_limbs(r_val)
        n = self.rns.native_modulus

        t = [0] * (2 * N - 1)
        for i in range(N):
            for j in range(N):
                t[i + j] = (t[i + j] + self[i] * other[j] + p[i] * q[j]) % n

        v0, v1 = self.residues(t, r)

        return Integer(self.rns, r), q, t, v0, v1

    def __add__(self, other):
        res = self.rns.from_limbs([(a + b) % self.native_modulus() for (a, b) in zip(self.limbs, other.limbs)])
        assert res.value() == self.value() + other.value()
        return res

    def __sub__(self, other):
        n = self.rns.native_modulus
        aux = self.rns.aux
        r = [(a - b) % n for a, b in zip(self, other)]
        r = [(r + aux) % n for r, aux in zip(r, aux)]
        r = self.rns.from_limbs(r)
        return r.reduce()

    def __getitem__(self, i):
        return self.limbs[i]

    def apply_positive_aux(self):
        return self.rns.from_limbs([self.limbs[i] + self.rns.aux[i] for i in range(self.rns.number_of_limbs)])

    def apply_negative_aux(self):
        return self.rns.from_limbs([self.rns.aux[i] - self.limbs[i] for i in range(self.rns.number_of_limbs)])

    def reduce(self):
        p = self.wrong_modulus()
        value = self.value()

        q = value // p
        r_val = value % p
        p = self.rns.neg_wrong_modulus_limbs()
        r = self.rns.value_to_limbs(r_val)

        t = [_a + q * _p for (_a, _p) in zip(self.limbs, p)]
        v0, v1 = self.residues(t, r)

        return Integer(self.rns, r), q, t, v0, v1

    def residues(self, t, r):

        t_correct = t[:]
        b = self.rns.bit_len_limb
        T = self.rns.T

        for i, ri in enumerate(r):
            t_correct[i] = t[i] - ri

        acc = 0
        for i, ti in enumerate(t_correct):
            acc = acc + (ti << (b * i))
        assert acc % T == 0

        n = self.rns.native_modulus
        mask = self.rns.lsh(1, 2) - 1
        rns = self.rns

        u0 = (t[0] + rns.lsh(t[1]) - r[0] - rns.lsh(r[1]))
        u0_ = (t[0] + (t[1] << b)) - r[0] - (r[1] << b)

        u1 = (t[2] + rns.lsh(t[3]) - r[2] - rns.lsh(r[3]))
        u1_ = (t[2] + (t[3] << b)) - r[2] - (r[3] << b)
        assert u0_ < n
        assert u1_ < n
        # print("u", hex(u0))
        # print("u", hex(u1))

        u1 = (u1 + rns.rsh(u0, 2))
        # print("u", hex(u1))

        assert u0 & mask == 0
        assert u1 & mask == 0

        v0 = rns.rsh(rns.rsh(u0))
        v1 = rns.rsh(rns.rsh(u1))

        return v0, v1

    def value(self):
        return self.rns.value_from_limbs(self.limbs)

    def native(self):
        return self.value() % self.rns.native_modulus

    def wrong_modulus(self):
        return self.rns.wrong_modulus

    def native_modulus(self):
        return self.rns.native_modulus

    def debug(self, desc=""):
        s = desc + ": " + hex(self.value()) + "\n" + "["
        for e in self.limbs:
            s += hex(e) + ", "
        print(s, "]")
