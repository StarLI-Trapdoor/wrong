# Wrong Field

This uncomplete and draft wrong field implementation spec is mostly targetting ~256 bit base field on ~256 bit operation field such as BN254, secpk256 base fields on BN254 scalar field.

And [solution from AZTEC](https://hackmd.io/@arielg/B13JoihA8) team is closely followed.

In layouts we use simple standart 4 width plonk gate with single further cell customization in `column_d`.

```
a * q_a + b * q_b + a * b * q_mul + c * q_c + d * q_d + d_next * q_d_next + q_constant = 0
```

## Definitions

`number_of_limbs`: For now we are only considering 4 limbs.

`b`: In sake of simplycity and convention limbs will be 64 bit.

`B = 1 << b`

`n`: Native field modulus.

`p`: Wrong field modulus.

`t = 256`

`T = 2^256`

`number_of_limbs_lookup`: to follow simplified approach above number of limbs for limb decomposion will be 4.

`b_lookup`: Again to follow simplified approach above number of lookup limbs will be `b/number_of_limbs_lookup = 16`.

`L = 1 << b_lookup`

> SEARCH: Where 68 bit limb and 110 bit overflow size comes from?

### Integer

An integer `a` is represented with 4 limbs `a = [a_3, a_2, a_1, a_0]`. Where it's actually a decomposion `a = a_3 * B^3 + a_2 * B^2 a_1 * B + a_0`.

`p' = T - p = [p'_3, p'_2, p'_1, p'_0]`

We mostly expect that an integer `a < T` and call it prenormalized integer while normalized integer satisfies `a < p`.

## Range

We will need to constaint some cells to be in `[0,B)` or `[0,B + overflow]`. Notice that `B = 4 * (1 << b_lookup)` and then we decompose `b` bit value into 4 `b_lookup` values. Overflow part of the range is smaller than a lookup chunk so let's  `b_overflow < b_lookup`.

`u = (u_3 * L^3 + u_2 * L^2 * u_1 * L + u_0) + L^4 * overflow`.

To constain an integer to be in prenormalized form `a < T` rather than the to be an actual field element `a < p`. So each limb of and integer is decomposed in smaller 4 chunks. And these chunks are checked if they are in lookup table and then we recompose the limb with values int the table and check if it is equal to proposed limb.

### Layout

Notice that we will use further cells in `column_d` to check recomposition.

| A  | B  | C        | D  |
| -- | -- | -------- | -- |
| u1 | u2 | u3       | u4 |
| -  | -  | overflow | u  |

## Addition

Addition is straight forward:

`c = a + b = [a_i + b_i]`

Modular reduction is not neccerarily applied right after the addition. It leaves us some room for lazy operations. So maximum bit lenght of the result is increased by 1. So if a and b is pre nor

### Layout of addition

| A  | B  | C  | D |
| -- | -- | -- | - |
| a1 | b1 | c1 | - |
| a2 | b2 | c1 | - |
| a3 | b3 | c1 | - |

## Prenormalize

`a = q * p + r`

* constrain `q` to be in `[0 ,B)`.
* constrain `r_i` to be in `[0, B)`.

So we don't apply a strict reduction. In general case

```
a = (q - β) * p + (r + β * p)
q' = (q - β)
r' = (r + β * p)
```

We require prover to increment `β` if `q` is not in `[0 ,B)`. Therefore result `r` is in `[0, T)`.

```
t_0 = a_0 + p'_0 * q
t_1 = a_1 + p'_1 * q
t_2 = a_2 + p'_2 * q
t_3 = a_3 + p'_3 * q
u_0 = t_0 + t_1 * B - r_0 - r_1 * B
u_1 = t_2 + t_3 * B - r_2 - r_3 * B
```

* constrain first `2b` bits of `u_0` is zero
* constrain first `2b` bits of `u_1 + u_0 / R^2` is zero

```
v_0 = u_0 / R^2
v_1 = (u_1 + u_0 / R^2) / R^2
```

* constain `v_0` is in `[0, B + overflow_0)`
* constain `v_1` is in `[0, B + overflow_1)`

> TODO: about `overflow_i` values in __prenormalization__

> TODO: about quotient adjustment.

### Layout of prenormalization

| A   | B   | C   | D   |
| --- | --- | --- | --- |
| a_0 | q   | t_0 | -   |
| a_1 | q   | t_1 | -   |
| a_2 | q   | t_2 | -   |
| a_3 | q   | t_3 | -   |
| t_0 | t_1 | r_0 | r_1 |
| -   | -   | v_0 | u_0 |
| t_2 | t_3 | r_0 | r_1 |
| -   | -   | v_0 | u_1 |

Note that range checks are not in the layout.

## Subtraction

We apply subtraction as `c = a - b + p * aux` with a range correction aux value where moves result limbs to the correct range. `aux` value is calculated as

`k = B - 1`
`aux = [p'_i * k]`

If `p'_i` is zero we just borrow from next limb and we can assume minimum `aux_i` is equal to `k` and maximum `aux_i` is equal to `k*k`. and also notice that maximum value of a prenormalized limb is also equal to `k`. We can write down this as  `aux_i` is in `(B,2B)`.

`c = a - b = [a_i - b_i + aux_i]`

So, corrected result `c_i` will be in `[0,2B)`.

> RESEARCH: solution above works for general cases and we can also use smaller `aux_i` when modulus is predefined.

To continiue working with same integer we apply prenormalization to the intermediate result `c` in order to reduce the result in `[0,T)`. In this prenormalization we will constrain `q` in `[0, B)`.

### Layout of subtraction

| A  | B  | C  | D |
| -- | -- | -- | - |
| a1 | b1 | c1 | - |
| a2 | b2 | c1 | - |
| a3 | b3 | c1 | - |

Notice that `p * aux` is constant and values are placed in fixed columns.

## Multiplication

Multiplication will be constrained as `a * b = q * p + r` where `q` and `r` witness values. Notice that prover also can use shifted quotient and result values as it also happens in subtraction.

```
a = (q - β) * p + (r + β * p)
q' = (q - β)
r' = (r + β * p)
```

* constaint `q'_i` in `[0, B)`
* constaint `r'_i` in `[0, B)`

With that range constaints however we are sure that our result is in `[0, T)`. Which is sufficient to work with result integer in all operations.

Here we rewrite intermediate value equations as in AZTEC solution.

```
t_0 = a_0 * b_0 + p'_0 * q_0
t_1 = a_0 * b_1 + a_1 * b_0 + p'_0 * q_1 + p'_1 * q_0
t_2 = a_0 * b_2 + a_1 * b_1 + a_2 * b_0 + p'_0 * q_2 + p'_1 * q_1 + p'_2 * q_0
t_3 = a_0 * b_3 + a_1 * b_2 + a_2 * b_1 + a_3 * b_0 + p'_0 * q_3 + p'_1 * q_2 + p'_2 * q_1 + p'_3 * q_0
```

After having intermediate values the rest goes same as we did in prenormalization except different overflow range constaints.

> TODO: about `overflow_i` values in __multiplication__

### Layout of multiplication

| A   | B   | C   | D     |
| --- | --- | --- | ----- |
| a_0 | b_0 | q_0 | t_0   |
| a_0 | b_1 | q_1 | t_1   |
| a_1 | b_0 | q_0 | tmp   |
| a_0 | b_2 | q_2 | t_2   |
| a_1 | b_1 | q_1 | tmp_a |
| a_2 | b_0 | q_0 | tmp_b |
| a_0 | b_3 | q_3 | t_3   |
| a_1 | b_1 | q_2 | tmp_b |
| a_2 | b_2 | q_1 | tmp_a |
| a_3 | b_0 | q_0 | tmp_c |
| t_0 | t_1 | r_0 | r_1   |
| -   | -   | v_0 | u_0   |
| t_0 | t_1 | r_0 | r_1   |
| -   | v_1 | v_0 | u_1   |
