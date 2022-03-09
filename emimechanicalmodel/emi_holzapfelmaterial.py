"""

Åshild Telle / Simula Research Laboratiry / 2021

"""

import dolfin as df
import ufl

from .holzapfelmaterial import HolzapfelMaterial
from .mesh_setup import assign_discrete_values


class EMIHolzapfelMaterial:
    """

    Adaption of Holzapfel material model to the EMI framework; simply let all material parameters
    be discrete functions, assigned to be zero for anisotropic terms.

    Args:
        U - function space for discrete function; DG-0 is a good choice
        subdomain_map - mapping from volume array to U; for DG-0 this is trivial
        a_i ... b_if - material properties; see paper    

    """
    def __init__(
        self,
        U,
        subdomain_map,
        a_i=df.Constant(0.074),
        b_i=df.Constant(4.878),
        a_e=df.Constant(1),
        b_e=df.Constant(10),
        a_if=df.Constant(4.071),
        b_if=df.Constant(5.433),
        a_esn=df.Constant(1.0),
        b_esn=df.Constant(5.0),
    ):
        # assign material paramters via characteristic functions
        xi_i = df.Function(U)
        assign_discrete_values(xi_i, subdomain_map, 1, 0)
        
        xi_e = df.Function(U)
        assign_discrete_values(xi_e, subdomain_map, 0, 1)

        a = a_i*xi_i + a_e*xi_e
        b = b_i*xi_i + b_e*xi_e
        a_f = a_if*xi_i
        b_f = b_if        # set everywhere to avoid division by zero error

        a_s = a_esn*xi_e
        b_s = b_esn

        # these are df.Constants, which can be changed from the outside
        self.a_i, self.a_e, self.b_i, self.b_e, self.a_if, self.b_if, self.a_esn, self.b_esn = \
                a_i, a_e, b_i, b_e, a_if, b_if, a_esn, b_esn

        # these are fenics functions defined over all of omega, not likely to be accessed
        self._a, self._b, self._a_f, self._b_f, self._a_s, self._b_s = a, b, a_f, b_f, a_s, b_s


    def passive_component(self, F):
        
        a, b, a_f, b_f, a_fs, b_fs = (
            self._a,
            self._b,
            self._a_f,
            self._b_f,
            self._a_s,
            self._b_s,
        )
        
        e1 = df.as_vector([1.0, 0.0, 0.0])
        e2 = df.as_vector([0.0, 1.0, 0.0])
        e3 = df.as_vector([0.0, 0.0, 1.0])

        J = df.det(F)
        C = pow(J, -float(2) / 3) * F.T * F

        IIFx = df.tr(C)
        I4e1 = df.inner(C * e1, e1)
        I4e2 = df.inner(C * e2, e2)
        I4e3 = df.inner(C * e3, e3)

        cond = lambda a: ufl.conditional(a > 0, a, 0)

        W_hat = a / (2 * b) * (df.exp(b * (IIFx - 3)) - 1)
        W_f = a_f / (2 * b_f) * (df.exp(b_f * cond(I4e1 - 1) ** 2) - 1)

        W_fs = a_fs / (2 * b_fs) * (df.exp(b_f * cond(I4e2 - 1) ** 2) - 1) + \
             + a_fs / (2 * b_fs) * (df.exp(b_f * cond(I4e3 - 1) ** 2) - 1)

        return W_hat + W_f + W_fs
