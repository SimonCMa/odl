# Copyright 2014-2017 The ODL contributors
#
# This file is part of ODL.
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at https://mozilla.org/MPL/2.0/.

"""Entry points for adding more spaces to ODL using external packages.

External packages can add implementations of `NtuplesBase` and `FnBase` by
hooking into the setuptools entry point ``'odl.space'`` and exposing the
methods ``ntuples_impls`` and ``fn_impls``.

This is used with functions such as `rn`, `fn` and `uniform_discr` in order
to allow arbitrary implementations.

See Also
--------
NumpyFn : Numpy based implementation of `FnBase`
NumpyNtuples : Numpy based implementation of `NtuplesBase`
"""

# Imports for common Python 2/3 codebase
from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

from pkg_resources import iter_entry_points
from odl.space.npy_ntuples import NumpyNtuples, NumpyFn

__all__ = ('ntuples_impl_names', 'fn_impl_names',
           'ntuples_impl', 'fn_impl')


IS_INITIALIZED = False
NTUPLES_IMPLS = {'numpy': NumpyNtuples}
FN_IMPLS = {'numpy': NumpyFn}


def _initialize_if_needed():
    """Initialize ``NTUPLES_IMPLS`` and ``FN_IMPLS`` if not already done."""
    global IS_INITIALIZED, NTUPLES_IMPLS, FN_IMPLS
    if not IS_INITIALIZED:
        for entry_point in iter_entry_points(group='odl.space', name=None):
            try:
                module = entry_point.load()
                NTUPLES_IMPLS.update(module.ntuples_impls())
                FN_IMPLS.update(module.fn_impls())
            except ImportError:
                pass
        IS_INITIALIZED = True


def ntuples_impl_names():
    """A list of strings with valid ntuples implementation names."""
    _initialize_if_needed()
    return list(NTUPLES_IMPLS.keys())


def fn_impl_names():
    """A list of strings with valid fn implementation names."""
    _initialize_if_needed()
    return list(FN_IMPLS.keys())


def ntuples_impl(impl):
    """N-tuples class corresponding to key.

    Parameters
    ----------
    impl : `str`
        Name of the implementation, see `ntuples_impl_names` for full list.

    Returns
    -------
    ntuples_imple : `type`
        Class inheriting from `NtuplesBase`.
    """
    if impl != 'numpy':
        # Shortcut to improve "import odl" times since most users do not use
        # non-numpy backend.
        _initialize_if_needed()

    return NTUPLES_IMPLS[impl]


def fn_impl(impl):
    """Fn class corresponding to key.

    Parameters
    ----------
    impl : `str`
        Name of the implementation, see `fn_impl_names` for full list.

    Returns
    -------
    ntuples_imple : `type`
        Class inheriting from `FnBase`.
    """
    if impl != 'numpy':
        # Shortcut to improve "import odl" times since most users do not use
        # non-numpy backend.
        _initialize_if_needed()

    return FN_IMPLS[impl]
