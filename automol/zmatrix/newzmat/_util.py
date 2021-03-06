"""
  Util functions for ts.py
"""

import functools
import numpy
from qcelemental import constants as qcc
import automol


def reorder_zmatrix_for_redef(zma, a_idx, h_idx,
                              frm_bnd_keys, brk_bnd_keys):
    """ performs z-matrix reordering operations required to
        build proper z-matrices for hydrogen migrations
    """

    # initialize zmat components needed later
    symbols = automol.zmatrix.symbols(zma)

    # Get the longest chain for all the atoms
    _, gras = shifted_standard_zmas_graphs([zma], remove_stereo=True)
    gra = functools.reduce(automol.graph.union, gras)
    xgr1, = automol.graph.connected_components(gra)
    chains_dct = automol.graph.atom_longest_chains(xgr1)

    # find the longest heavy-atom chain for the forming atom
    form_chain = chains_dct[a_idx]

    # get the indices used for reordering
    # get the longest chain from the bond forming atom (not including H)
    order_idxs = [idx for idx in form_chain
                  if symbols[idx] != 'H' and idx != h_idx]

    # add all the heavy-atoms not in the chain
    for i, atom in enumerate(symbols):
        if i not in order_idxs and atom != 'H':
            order_idxs.append(i)

    # add all the hydrogens
    for i, atom in enumerate(symbols):
        if i != h_idx and atom == 'H':
            order_idxs.append(i)

    # add the migrating atoms
    order_idxs.append(h_idx)

    # get the geometry and redorder it according to the order_idxs list
    geo = [list(x) for x in automol.zmatrix.geometry(zma)]
    geo2 = tuple(tuple(geo[idx]) for idx in order_idxs)

    # Convert the reordered geometry into a zma
    print('init_geo2\n', automol.geom.string(geo2))
    zma2 = automol.geom.zmatrix(geo2)

    # Convert the frm and brk keys
    order_dct = automol.geom.zmatrix_atom_ordering(geo2)
    frm_bnd_keys = frozenset(order_dct[x] for x in frm_bnd_keys)
    brk_bnd_keys = frozenset(frozenset(order_dct[x] for x in keys)
                             for keys in brk_bnd_keys)
    # brk_bnd_keys = frozenset(order_dct[x] for x in brk_bnd_keys)

    return zma2, frm_bnd_keys, brk_bnd_keys


def include_babs3(frm_bnd, rct2_gra):
    """Should we include babs3?
    """
    include = False
    atm_ngbs = automol.graph.atom_neighbor_keys(rct2_gra)
    is_terminal = False
    for atm in list(frm_bnd):
        if atm in atm_ngbs:
            if len(atm_ngbs[atm]) == 1:
                is_terminal = True
    if len(atm_ngbs.keys()) > 2 and is_terminal:
        include = True
    return include


def shifted_standard_zmas_graphs(zmas, remove_stereo=False):
    """ Generate zmas and graphs from input zmas
        shfited and in their standard form
    """
    zmas = list(zmas)
    conv = functools.partial(
        automol.convert.zmatrix.graph, remove_stereo=remove_stereo)
    gras = list(map(conv, zmas))
    shift = 0
    for idx, (zma, gra) in enumerate(zip(zmas, gras)):
        zmas[idx] = automol.zmatrix.standard_form(zma, shift=shift)
        gras[idx] = automol.graph.transform_keys(gra, lambda x: x+shift)
        shift += len(automol.graph.atoms(gra))
    zmas = tuple(zmas)
    gras = tuple(map(automol.graph.without_dummy_atoms, gras))
    return zmas, gras


def join_atom_keys(zma, atm1_key):
    """ returns available join atom keys (if available) and a boolean
    indicating whether the atoms are in a chain or not
    """
    gra = automol.convert.zmatrix.graph(zma)
    atm1_chain = (
        automol.graph.atom_longest_chains(gra)[atm1_key])
    atm1_ngb_keys = (
        automol.graph.atom_neighbor_keys(gra)[atm1_key])
    if len(atm1_chain) == 1:
        atm2_key = None
        atm3_key = None
        chain = False
    elif len(atm1_chain) == 2 and len(atm1_ngb_keys) == 1:
        atm2_key = atm1_chain[1]
        atm3_key = None
        chain = False
    elif len(atm1_chain) == 2:
        atm2_key = atm1_chain[1]
        atm3_key = sorted(atm1_ngb_keys - {atm2_key})[0]
        chain = False
    else:
        atm2_key, atm3_key = atm1_chain[1:3]
        chain = True

    return atm2_key, atm3_key, chain


def reorder_zma_for_radicals(zma, rad_idx):
    """ Creates a zmatrix where the radical atom is the first entry
        in the zmatrix
    """
    geo = automol.zmatrix.geometry(zma)
    geo_swp = automol.geom.swap_coordinates(geo, 0, rad_idx)
    zma_swp = automol.geom.zmatrix(geo_swp)

    return zma_swp


def shift_vals_from_dummy(vals, zma):
    """ Shift a set of values using remdummy
        Shift requires indices be 1-indexed
    """
    type_ = type(vals)

    dummy_idxs = automol.zmatrix.atom_indices(zma, sym='X')

    shift_vals = []
    for val in vals:
        shift = 0
        for dummy in dummy_idxs:
            if val >= dummy:
                shift += 1
        shift_vals.append(val+shift)

    shift_vals = type_(shift_vals)

    return shift_vals


def sort_zma_idxs(rct_zmas, prd_zmas, rxn_idxs):
    """ zma idxs
    """

    rct_idxs, prd_idxs = rxn_idxs
    rct_zmas = list(map(rct_zmas.__getitem__, rct_idxs))
    prd_zmas = list(map(prd_zmas.__getitem__, prd_idxs))

    return rct_zmas, prd_zmas


def rct1_x_join(rct1_zma, atm1_key, atm2_key, atm3_key):
    """ Build the R1+X matrix for bimol reactions
    """

    x_zma = ((('X', (None, None, None), (None, None, None)),), {})

    x_join_val_dct = {
        'rx': 1. * qcc.conversion_factor('angstrom', 'bohr'),
        'ax': 90. * qcc.conversion_factor('degree', 'radian'),
        'dx': 180. * qcc.conversion_factor('degree', 'radian'),
    }

    x_join_keys = numpy.array(
        [[atm1_key, atm2_key, atm3_key]])
    x_join_names = numpy.array([['rx', 'ax', 'dx']],
                               dtype=numpy.object_)
    x_join_names[numpy.equal(x_join_keys, None)] = None
    x_join_name_set = set(numpy.ravel(x_join_names)) - {None}
    x_join_val_dct = {name: x_join_val_dct[name]
                      for name in x_join_name_set}

    rct1_x_zma = automol.zmatrix.join(
        rct1_zma, x_zma, x_join_keys, x_join_names, x_join_val_dct)

    return rct1_x_zma


# def _rct2_x_join():
#     """
#     """


def rct1x_rct2_join(rct1_x_zma, rct2_zma,
                    dist_name, dist_val,
                    jkey1, jkey2, jkey3,
                    join_vals=(85., 85., 170., 85., 170.)):
    """ Second join function
    """

    rct2_natms = automol.zmatrix.count(rct2_zma)

    join_val_dct = {
        dist_name: dist_val,
        'aabs1': 85. * qcc.conversion_factor('degree', 'radian'),
        'aabs2': 85. * qcc.conversion_factor('degree', 'radian'),
        'babs1': 170. * qcc.conversion_factor('degree', 'radian'),
        'babs2': 85. * qcc.conversion_factor('degree', 'radian'),
        'babs3': 170. * qcc.conversion_factor('degree', 'radian'),
    }

    join_keys = numpy.array(
        [[jkey1, jkey2, jkey3],
         [None, jkey1, jkey2],
         [None, None, jkey1]])[:rct2_natms]
    join_names = numpy.array(
        [[dist_name, 'aabs1', 'babs1'],
         [None, 'aabs2', 'babs2'],
         [None, None, 'babs3']])[:rct2_natms]
    join_names[numpy.equal(join_keys, None)] = None

    join_name_set = set(numpy.ravel(join_names)) - {None}
    join_val_dct = {name: join_val_dct[name] for name in join_name_set}

    rct1_x_rct2_zma = automol.zmatrix.join(
        rct1_x_zma, rct2_zma, join_keys, join_names, join_val_dct)

    return rct1_x_rct2_zma
