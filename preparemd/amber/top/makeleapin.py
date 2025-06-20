import os
import re
import shutil

from loguru import logger

from preparemd.amber.top import leapin
from preparemd.utils.log import log_setup

log_setup(level="INFO")


def filecopy(val: list, distdir: str) -> None:
    """Validate file paths in a list and copy them to the distdir
    Args:
        val (list): List of file paths to validate and copy.
        distdir (str): Directory where files will be copied.
    Raises:
        ValueError: If any file in the list does not exist.
    """
    if val is not None:
        for i in val:
            if not os.path.exists(i):
                logger.error(f"Could not find {i}.")
                raise ValueError(f"Could not find {i}.")
            else:
                logger.info(f"Copying {i} to the top directory")
                shutil.copy2(i, os.path.join(distdir, "top"))


def filecopy_mol2(mol2: list, distdir: str) -> None:
    if mol2 is not None:
        for i in mol2:
            if "loadMol2" not in i:
                logger.error(f"'loadMol2' was not detected in str, {i}.")
                raise ValueError(f"'loadMol2' was not detected in str, {i}.")

            filepath = [a for a in re.split("=| |loadMol2", i) if a != ""][1]
            if not os.path.exists(filepath):
                logger.error(f"Could not find {filepath}.")
                raise ValueError(f"Could not find {filepath}.")
            else:
                logger.info(f"Copying {filepath} to the top directory")
                shutil.copy2(filepath, os.path.join(distdir, "top"))


def makeleapin(
    distdir: str,
    boxsize: str,
    pre2boxsize: str,
    ion_conc: float,
    sslink_file: str,
    fftype: str,
    frcmod: list,
    prep: list,
    mol2: list,
) -> None:
    """make a leap.in file
    パラメータファイル（frcmod, prep, mol2）はdistdir内にコピーする
    """
    if not os.path.exists(os.path.join(distdir)):
        os.makedirs(os.path.join(distdir))
    leapinfile = os.path.join(distdir, "top", "leap.in")

    filecopy(frcmod, distdir)
    filecopy(prep, distdir)
    filecopy_mol2(mol2, distdir)

    leapininput = leapin.leapininput(
        boxsize, pre2boxsize, ion_conc, sslink_file, fftype, frcmod, prep, mol2
    )

    with open(leapinfile, mode="w") as f:
        f.write(leapininput)
