from preparemd.amber.md.prepareinputs import _get_residues_from_pdb


def test_get_residues_from_pdb():
    pdbfile = "testfiles/1lke_af3/pre2.pdb"
    residues = _get_residues_from_pdb(pdbfile)
    assert residues == 363
