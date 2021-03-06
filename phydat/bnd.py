""" Dictionary of standard bond lengths
"""

from phydat.phycon import ANG2BOHR


def read_len(bnd_atoms):
    """ Read the dct
    """
    bnd_len = LEN_DCT.get(bnd_atoms, None)
    if bnd_len is None:
        bnd_atoms_flip = (bnd_atoms[1], bnd_atoms[0])
        bnd_len = LEN_DCT.get(bnd_atoms_flip, None)

    return bnd_len


# Dictionary of A-B single bond lengths
LEN_DCT = {
    ('H', 'H'): 0.74 * ANG2BOHR,
    ('H', 'C'): 1.09 * ANG2BOHR,
    ('H', 'N'): 1.01 * ANG2BOHR,
    ('H', 'O'): 0.95 * ANG2BOHR,
    ('H', 'Cl'): 1.275 * ANG2BOHR,
    ('C', 'C'): 1.54 * ANG2BOHR,
    ('C', 'N'): 1.47 * ANG2BOHR,
    ('C', 'O'): 1.43 * ANG2BOHR,
    ('N', 'N'): 1.45 * ANG2BOHR,
    ('N', 'O'): 1.45 * ANG2BOHR,
    ('O', 'O'): 1.40 * ANG2BOHR,
    ('C', 'Cl'): 1.74 * ANG2BOHR,
    ('Cl', 'Cl'): 2.0 * ANG2BOHR,
}
