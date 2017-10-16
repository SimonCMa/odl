"""Phase contrast TEM reconstruction example."""

# Imports for common Python 2/3 codebase
from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import super

import numpy as np
import odl
from intensity_op import IntensityOperator


def pupil_function(x, **kwargs):
    """Indicator function for the disc-shaped aperture, a.k.a. pupil function.


    Notes
    -----
    The pupil fuction is defined as

    .. math::

        A_\\Sigma(\\xi) = \\begin{cases}1,& \\Big\\|\\frac{f}{k}\\xi\\Big\\|
        \\leq r\\\\ 0,& \\Big\\|\\frac{f}{k}\\xi\\Big\\| > r \\end{cases}

    where :math:`\kappa` is the wave number of the incoming electron wave,
    :math:`r` is the radius of the aperture and :math:`f` is the focal length
    of the principal lens.
    """
    aper_rad = kwargs.pop('aper_rad')
    focal_length = kwargs.pop('focal_length')
    wave_number = kwargs.pop('wave_number')
    scaled_rad = aper_rad * wave_number / focal_length

    norm_sq = np.sum(xi ** 2 for xi in x[1:])

    return norm_sq <= scaled_rad ** 2


def optics_imperfections(x, **kwargs):
    """Function encoding the phase shifts due to optics imperfections.


    Notes
    -----
    The optics-imperfections function is defined as

    .. math::

        O(\\xi) = e^{iW(||\\xi\\|^2)},

    where the function :math:`W` is defined as

    .. math::

        W(t) = -\\frac{1}{4k}t\\left(\\frac{C_s}{k^2}t-2\\Delta z\\right),

    and where :math:`\kappa` is the wave number of the incoming electron wave,
    :math:`C_s` is the third-order spherical abberation of the lens and
    :math:`\\Delta z` is the defocus."""
    wave_number = kwargs.pop('wave_number')
    spherical_abe = kwargs.pop('spherical_abe')
    defocus = kwargs.pop('defocus')

    norm_sq = np.sum(xi ** 2 for xi in x[1:])
    # Rescale the length of the vector to account for larger detector in this
    # 2D toy example
    norm_sq *= (30 / (det_size / M * 100)) ** 2

    result = - (1 / (4 * wave_number)) * norm_sq * (norm_sq * spherical_abe /
                                                    wave_number ** 2 - 2 *
                                                    defocus)
    result = np.exp(1j * result)

    return result


def modulation_transfer_function(x, **kwargs):
    """Function that characterizes the detector response.


    Notes
    -----
    The modulation transfer function is defined as

    .. math::

        MTF(\\xi) = \\frac{a}{1 + \\alpha\\|\\xi\\|^2} +
        \\frac{b}{1+\\beta\\|\\xi\\|^2}+c

    where :math:`a,b,c,\\alpha` and :math:`\\beta` are real parameters."""
    a = kwargs.pop('mtf_a')
    b = kwargs.pop('mtf_b')
    c = kwargs.pop('mtf_c')
    alpha = kwargs.pop('mtf_alpha')
    beta = kwargs.pop('mtf_beta')

    norm_sq = np.sum(xi ** 2 for xi in x[1:]) / M**2

    result = a / (1 + alpha * norm_sq) + b / (1 + beta * norm_sq) + c

    return result


# %%

#  Define some physical constants
e_mass = 9.11e-31  # kg
e_charge = 1.602e-19  # C
planck_bar = 1.059571e-34  # Js/rad

wave_length = 0.0025e-9  # m
wave_number = 2 * np.pi / wave_length

sigma = e_mass * e_charge / (wave_number * planck_bar ** 2)

total_dose = 5000 * 1e18  # total electron dose per m^2
dose_per_img = total_dose / 61
gain = 80  # average nr of digital counts per incident electron

# Define sample diameter and height (we take the height at the edge)
sample_diam = 1200e-9  # m
sample_height = 150e-9  # m

# Define properties of the optical system
# Set focal_length to be the focal_length of the principal (first) lens !
M = 25000.0
aper_rad = 0.5*40e-6  # m
focal_length = 2.7e-3  # m
spherical_abe = 2.1e-3  # m
defocus = 3e-6  # m

# Define constants defining the modulation transfer function
mtf_a = 0.7
mtf_b = 0.2
mtf_c = 0.1
mtf_alpha = 10
mtf_beta = 40

# Set size of detector pixels (before rescaling to account for magnification)
det_size = 16e-6  # m
det_area = det_size **2  # m^2

reco_space = odl.uniform_discr(min_pt=[-20]*3,
                               max_pt=[20]*3,
                               shape=[300] * 3, dtype='complex128')


# Make a parallel beam geometry with flat detector
# Angles: uniformly spaced, n = 61, min = -pi/3, max = pi /3
angle_partition = odl.uniform_partition(-np.pi/3, np.pi/3, 61)
# Detector: uniformly sampled, n = (558, 558), min = (-30, -30), max = (30, 30)

detector_partition = odl.uniform_partition([-30] * 2,
                                           [30] * 2, [200] * 2)


geometry = odl.tomo.Parallel3dAxisGeometry(angle_partition, detector_partition)
ray_trafo = odl.tomo.RayTransform(reco_space, geometry)
scattering_op = ray_trafo.range.one() + 0.01j * ray_trafo

ft_ctf = odl.trafos.FourierTransform(scattering_op.range, axes=[1, 2])
pupil = ft_ctf.range.element(pupil_function, aper_rad=aper_rad,
                             wave_number=wave_number,
                             focal_length=focal_length)

optics_imperf = ft_ctf.range.element(optics_imperfections,
                                     wave_number=wave_number,
                                     spherical_abe=spherical_abe,
                                     defocus=defocus)

# Leave out pupil-function since it has no effect
ctf = optics_imperf
optics_op = ft_ctf.inverse * ctf * ft_ctf

intens_op = IntensityOperator(optics_op.range)

ft_det = odl.trafos.FourierTransform(intens_op.range, axes=[1, 2])
mtf = ft_det.range.element(modulation_transfer_function, mtf_a=mtf_a,
                           mtf_b=mtf_b, mtf_c=mtf_c, mtf_alpha=mtf_alpha,
                           mtf_beta=mtf_beta)
det_op = det_area * dose_per_img * gain * ft_det.inverse * mtf * ft_det

# Leave out det_op first, need to check that MTF does what it should
forward_op = intens_op * optics_op * scattering_op

phantom = (1+1j) * odl.phantom.shepp_logan(reco_space, modified=True)

data = forward_op(phantom)

reco = reco_space.zero()
callback = (odl.solvers.CallbackPrintIteration() &
            odl.solvers.CallbackShow())
odl.solvers.conjugate_gradient_normal(forward_op, reco, data,
                                      niter=10, callback=callback)
# non-linear cg must be adapted to complex case
#func = odl.solvers.L2NormSquared(data.space).translated(data) * forward_op
#odl.solvers.conjugate_gradient_nonlinear(func, reco, line_search=1e0, callback=callback,
#                                         nreset=50)

#func = odl.solvers.L2NormSquared(data.space).translated(data) * forward_op
#odl.solvers.conjugate_gradient_nonlinear(func, reco, line_search=1e0, callback=callback,
#                                         nreset=50)


lin_at_one = forward_op.derivative(forward_op.domain.one())
backprop = lin_at_one.adjoint(data)