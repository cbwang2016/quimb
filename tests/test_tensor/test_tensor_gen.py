import pytest
from numpy.testing import assert_allclose

import quimb as qu
import quimb.tensor as qtn


class TestSpinHam1D:

    @pytest.mark.parametrize("cyclic", [False, True])
    def test_var_terms(self, cyclic):
        n = 8
        Hd = qu.ham_mbl(n, dh=0.77, seed=42, cyclic=cyclic)
        Ht = qtn.MPO_ham_mbl(n, dh=0.77, seed=42, cyclic=cyclic).to_dense()
        assert_allclose(Hd, Ht)

    @pytest.mark.parametrize("var_two", ['none', 'some', 'only'])
    @pytest.mark.parametrize("var_one", ['some', 'only', 'only-some',
                                         'def-only', 'none'])
    def test_specials(self, var_one, var_two):
        K1 = qu.rand_herm(2**1)

        n = 10
        HB = qtn.SpinHam1D(S=1 / 2)

        if var_two == 'some':
            HB += 1, K1, K1
            HB[4, 5] += 1, K1, K1
            HB[7, 8] += 1, K1, K1
        elif var_two == 'only':
            for i in range(n - 1):
                HB[i, i + 1] += 1, K1, K1
        else:
            HB += 1, K1, K1

        if var_one == 'some':
            HB += 1, K1
            HB[2] += 1, K1
            HB[3] += 1, K1
        elif var_one == 'only':
            for i in range(n - 1):
                HB[i] += 1, K1
        elif var_one == 'only-some':
            HB[1] += 1, K1
        elif var_one == 'def-only':
            HB += 1, K1

        HB.build_local_ham(n)
        H_mpo = HB.build_mpo(n)
        H_sps = HB.build_sparse(n)

        assert_allclose(H_mpo.to_dense(), H_sps.A)

    def test_no_default_term(self):
        N = 10
        builder = qtn.SpinHam1D(1 / 2)

        for i in range(N - 1):
            builder[i, i + 1] += 1.0, 'Z', 'Z'

        H = builder.build_mpo(N)

        dmrg = qtn.DMRG2(H)
        dmrg.solve(verbosity=1)

        assert dmrg.energy == pytest.approx(-2.25)


class TestMPSSpecificStates:

    @pytest.mark.parametrize("dtype", ['float32', 'complex64'])
    def test_ghz_state(self, dtype):
        mps = qtn.MPS_ghz_state(5, dtype=dtype)
        assert mps.dtype == dtype
        psi = qu.ghz_state(5, dtype=dtype)
        assert mps.H @ mps == pytest.approx(1.0)
        assert mps.bond_sizes() == [2, 2, 2, 2]
        assert qu.fidelity(psi, mps.to_dense()) == pytest.approx(1.0)

    @pytest.mark.parametrize("dtype", ['float32', 'complex64'])
    def test_w_state(self, dtype):
        mps = qtn.MPS_w_state(5, dtype=dtype)
        assert mps.dtype == dtype
        psi = qu.w_state(5, dtype=dtype)
        assert mps.H @ mps == pytest.approx(1.0)
        assert mps.bond_sizes() == [2, 2, 2, 2]
        assert qu.fidelity(psi, mps.to_dense()) == pytest.approx(1.0)

    def test_computational_state(self):
        mps = qtn.MPS_computational_state('01+-')
        assert_allclose(mps.to_dense(),
                        qu.up() & qu.down() & qu.plus() & qu.minus())


class TestGenericTN:

    def test_TN_rand_reg(self):
        n = 6
        reg = 3
        D = 2
        tn = qtn.TN_rand_reg(n, reg, D=D)
        assert tn.outer_inds() == ()
        assert tn.max_bond() == D
        assert {t.ndim for t in tn} == {reg}
        ket = qtn.TN_rand_reg(n, reg, D=2, phys_dim=2)
        assert set(ket.outer_inds()) == {f'k{i}' for i in range(n)}
        assert ket.max_bond() == D

    @pytest.mark.parametrize('Lx', [3])
    @pytest.mark.parametrize('Ly', [2, 4])
    @pytest.mark.parametrize('beta', [0.13, 0.44])
    @pytest.mark.parametrize('h', [0.0, 0.1])
    @pytest.mark.parametrize('cyclic',
                             [False, True, (False, True), (True, False)])
    def test_2D_classical_ising_model(self, Lx, Ly, beta, h, cyclic):
        tn = qtn.TN2D_classical_ising_partition_function(
            Lx, Ly, beta=beta, h=h, cyclic=cyclic)
        htn = qtn.HTN2D_classical_ising_partition_function(
            Lx, Ly, beta=beta, h=h, cyclic=cyclic)
        Z1 = tn.contract(all, output_inds=())
        Z2 = htn.contract(all, output_inds=())
        assert Z1 == pytest.approx(Z2)

    @pytest.mark.parametrize('Lx', [2])
    @pytest.mark.parametrize('Ly', [3])
    @pytest.mark.parametrize('Lz', [4])
    @pytest.mark.parametrize('beta', [0.13, 1 / 4.5])
    @pytest.mark.parametrize('h', [0.0, 0.1])
    @pytest.mark.parametrize('cyclic',
                             [False, True,
                              (False, True, False), (True, False, True)])
    def test_3D_classical_ising_model(self, Lx, Ly, Lz, beta, h, cyclic):
        tn = qtn.TN3D_classical_ising_partition_function(
            Lx, Ly, Lz, beta=beta, h=h, cyclic=cyclic)
        htn = qtn.HTN3D_classical_ising_partition_function(
            Lx, Ly, Lz, beta=beta, h=h, cyclic=cyclic)
        Z1 = tn.contract(all, output_inds=())
        Z2 = htn.contract(all, output_inds=())
        assert Z1 == pytest.approx(Z2)
