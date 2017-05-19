"""Define the LinearSystemComp class."""
from __future__ import division, print_function

from six.moves import range

import numpy as np
from scipy import linalg

from openmdao.core.implicitcomponent import ImplicitComponent


class Circulations(ImplicitComponent):
    """
    Component that solves a linear system, Ax=b.

    Designed to handle small and dense linear systems that can be
    efficiently solved with lu-decomposition

    Attributes
    ----------
    _lup : object
        matrix factorization returned from scipy.linag.lu_factor
    """

    def initialize(self):
        """
        Declare metadata.
        """
        self.metadata.declare('size', default=1, type_=int, desc='the size of the linear system')

    def initialize_variables(self):
        """
        Matrix and RHS are inputs, solution vector is the output.
        """
        size = self.metadata['size']

        self._lup = None

        self.add_input('AIC', val=np.eye(size))
        self.add_input('rhs', val=np.random.rand(size))
        self.add_output('circulations', shape=size, val=.1)

    def initialize_partials(self):
        """
        Set up the derivatives according to the user specified mode.
        """

        size = self.metadata['size']
        row_col = np.arange(size, dtype="int")

        arange = np.arange(size)
        self.declare_partials('circulations', 'rhs', val=-1., rows=arange, cols=arange)

    def apply_nonlinear(self, inputs, outputs, residuals):
        """
        R = Ax - b.

        Parameters
        ----------
        inputs : Vector
            unscaled, dimensional input variables read via inputs[key]
        outputs : Vector
            unscaled, dimensional output variables read via outputs[key]
        residuals : Vector
            unscaled, dimensional residuals written to via residuals[key]
        """
        residuals['circulations'] = inputs['AIC'].dot(outputs['circulations']) - inputs['rhs']

    def solve_nonlinear(self, inputs, outputs):
        """
        Use numpy to solve Ax=b for x.

        Parameters
        ----------
        inputs : Vector
            unscaled, dimensional input variables read via inputs[key]
        outputs : Vector
            unscaled, dimensional output variables read via outputs[key]
        """
        # lu factorization for use with solve_linear
        self._lup = linalg.lu_factor(inputs['AIC'])
        outputs['circulations'] = linalg.lu_solve(self._lup, inputs['rhs'])

    def linearize(self, inputs, outputs, J):
        """
        Compute the non-constant partial derivatives.
        """
        x = outputs['circulations']
        size = self.metadata['size']

        dx_dA = np.zeros((size, size**2))
        for i in range(size):
            dx_dA[i, i * size:(i + 1) * size] = x
        J['circulations', 'AIC'] = dx_dA

        J['circulations', 'circulations'] = inputs['AIC']

    def solve_linear(self, d_outputs, d_residuals, mode):
        r"""
        Back-substitution to solve the derivatives of the linear system.

        If mode is:
            'fwd': d_residuals \|-> d_outputs

            'rev': d_outputs \|-> d_residuals

        Parameters
        ----------
        d_outputs : Vector
            unscaled, dimensional quantities read via d_outputs[key]
        d_residuals : Vector
            unscaled, dimensional quantities read via d_residuals[key]
        mode : str
            either 'fwd' or 'rev'
        """
        if mode == 'fwd':
            sol_vec, rhs_vec = d_outputs, d_residuals
            t = 0
        else:
            sol_vec, rhs_vec = d_residuals, d_outputs
            t = 1

        # print("foobar", rhs_vec['circulations'])
        sol_vec['circulations'] = linalg.lu_solve(self._lup, rhs_vec['circulations'], trans=t)