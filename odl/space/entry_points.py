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
        # pkg_resources has long import time
        from pkg_resources import iter_entry_points
        for entry_point in iter_entry_points(group='odl.space', name=None):
            try:
                module = entry_point.load()
            except ImportError:
                pass
            else:
                NTUPLES_IMPLS.update(module.ntuples_impls())
                FN_IMPLS.update(module.fn_impls())
        IS_INITIALIZED = True


def ntuples_impl_names():
    """A tuple of strings with valid ntuples implementation names."""
    _initialize_if_needed()
    return tuple(NTUPLES_IMPLS.keys())


def fn_impl_names():
    """A tuple of strings with valid fn implementation names."""
    _initialize_if_needed()
    return tuple(FN_IMPLS.keys())


def ntuples_impl(impl):
    """N-tuples class corresponding to key.

    Parameters
    ----------
    impl : `str`
        Name of the implementation, see `ntuples_impl_names` for full list.

    Returns
    -------
    ntuples_impl : `type`
        Class inheriting from `NtuplesBase`.

    Raises
    ------
    ValueError
        If ``impl`` is not a valid name of a ntuples imlementation.
    """
    if impl != 'numpy':
        # Shortcut to improve "import odl" times since most users do not use
        # non-numpy backend.
        _initialize_if_needed()

    try:
        return NTUPLES_IMPLS[impl]
    except KeyError:
        raise ValueError("key '{}' does not correspond to a valid ntuples "
                         "implmentation".format(impl))


def fn_impl(impl):
    """Fn class corresponding to key.

    Parameters
    ----------
    impl : `str`
        Name of the implementation, see `fn_impl_names` for full list.

    Returns
    -------
    fn_impl : `type`
        Class inheriting from `FnBase`.

    Raises
    ------
    ValueError
        If ``impl`` is not a valid name of a fn imlementation.
    """
    if impl != 'numpy':
        # Shortcut to improve "import odl" times since most users do not use
        # non-numpy backend.
        _initialize_if_needed()

    try:
        return FN_IMPLS[impl]
    except KeyError:
        raise ValueError("key '{}' does not correspond to a valid fn "
                         "implmentation".format(impl))
