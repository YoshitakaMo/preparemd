#!/usr/bin/env pytyon3
# %%
import Bio.PDB
import os
import re
import subprocess
from absl import logging
from absl import app
from absl import flags

# %%


def getvalue(mdout, energyterm):
    """
    md.outのファイルから値を取り出す。
    """
    AVEline = int(
        subprocess.check_output(
            f"sed -n '/A V E R A G E S   O V E R/=' {mdout}", shell=True
        )
    )
    AVEline = str(AVEline)
    value = float(
        subprocess.check_output(
            "tail -n +"
            + AVEline
            + " "
            + mdout
            + " | head -n 10 | grep '"
            + energyterm
            + "' | awk '{print $9'}",
            shell=True,
        )
    )
    return value


def get_res_atom_number(pdbfile) -> tuple:
    """
    Biopythonを用いてイオンと水以外の残基数(residuenum)と全原子数(atomnum)を返す
    """
    residuenum = 0
    atomnum = 0
    pdb_parser = Bio.PDB.PDBParser(PERMISSIVE=True, QUIET=True)
    with open(pdbfile) as f:
        struc = pdb_parser.get_structure(" ", f)
    for model in struc:
        for chain in model:
            for res in chain:
                if res.get_resname() not in ["Na+", "Cl-", "WAT"]:
                    residuenum += 1
                for atom in res:
                    atomnum += 1

    return residuenum, atomnum


def make_amdin(
    ethreshp: float,
    alphap: float,
    ethreshd: float,
    alphad: float,
    nmropt: int,
    basedir: str,
    outdir: str,
    amdinputfile: str,
) -> None:
    """
    amd.inをoutput
    amd.inのテンプレート
    """
    amdincontent = f"""vt-continue
&cntrl
  imin=0,               ! Molecular dynamics
!  irest=0,              ! DO NOT restart MD simulation from a previous run.
!  ntx=1,                ! Coordinates and velocities will not be read
  irest=1,              ! Restart MD simulation from a previous run.
  ntx=5,                ! Coordinates and velocities will be read from a previous run.
  nstlim=10000000,      ! Number of MD steps
  dt=0.002,             ! Timestep (ps)
  ntc=2,                ! SHAKE on for bonds involving hydrogen atoms
  ntf=2,                ! No force evaluation for bonds with hydrogen
  ig=-1,                ! Random seed for Langevin thermostat
  cut=10.0,             ! Nonbonded cutoff (Angstroms)
  tol=0.000001          ! SHAKE tolerance
  ntb=2,                ! Constant pressure periodic boundary conditions
  ntp=1,                ! Isotropic pressure coupling
  ntpr=5000,            ! Print to mdout every ntpr steps
  ntwr=500000,          ! Every ntwr steps during dynamics, the "restrt" file will be written
  ntwx=5000,            ! Write to trajectory file every ntwc steps
  ntt=3,                ! Langevin thermostat
  gamma_ln=2.0,         ! Collision frequency for thermostat
  temp0=300.0,          ! Simulation temperature (K)
  ioutfm=1,             ! Write binary NetCDF trajectory
  iwrap=1,              ! the coordinates written to the restart and trajectory files will be "wrapped" into a primary box.
  iamd=3,               ! boost the whole potential with an extra boost to the torsions
  nmropt={nmropt},             ! turn on NMR restraints
  ethreshp={ethreshp:.2f}, alphap={alphap:.2f},
  ethreshd={ethreshd:.2f}, alphad={alphad:.2f},
  /
  &ewald
  dsum_tol=0.000001,
  /
  &wt
   type='DUMPFREQ', istep1=5000,
  /
  &wt type='END' /
 DISANG=dist1.rst
 DUMPAVE=dist1.dat
"""

    os.makedirs(os.path.join(basedir, outdir), exist_ok=True)
    amd_in_path = os.path.join(basedir, outdir, amdinputfile)
    with open(amd_in_path, "w") as f:
        f.write(amdincontent)


# %%
def make_runsh(basedir, indir, prerunfile, outdir, rstfile, amdrunfile) -> None:
    """
    prerunfileをコピーしてamd用のrun.shファイルを作成する
    """
    prerunfile_path = os.path.join(basedir, indir, prerunfile)
    if not os.path.exists(prerunfile_path):
        logging.error("Could not find run.sh file, %s", prerunfile_path)
        raise ValueError(f"Could not find run.sh file, {prerunfile_path}")
    with open(prerunfile_path) as f:
        prerunfile_content = f.read()

    relpath = os.path.relpath(
        os.path.join(basedir, indir), os.path.join(basedir, outdir)
    )
    runfile_content = re.sub(
        "rstfile=.*", f'rstfile="{relpath}/{rstfile}"', prerunfile_content
    )
    runfile_content = re.sub("md.in", "amd.in", runfile_content)

    os.makedirs(os.path.join(basedir, outdir), exist_ok=True)
    amdrunfile_path = os.path.join(basedir, outdir, amdrunfile)
    with open(amdrunfile_path, "w") as f:
        f.write(runfile_content)


# %%
def write_amdinputfile(
    basedir: str,
    indir: str,
    mdoutfile: str,
    outdir: str,
    amdinputfile: str,
    prerunfile: str,
    amdrunfile: str,
    topdir: str,
    pdbfile: str,
    rstfile: str,
    nmropt: int,
):
    """
    amd.inファイルを出力する
    """

    mdout_path = os.path.join(basedir, indir, mdoutfile)
    if not os.path.exists(mdout_path):
        logging.error("Could not find mdout file, %s", mdout_path)
        raise ValueError(f"Could not find mdout file, {mdout_path}")
    eptot = getvalue(mdout_path, "EPtot")
    dihed = getvalue(mdout_path, "DIHED")

    pdbfile_path = os.path.join(basedir, topdir, pdbfile)
    if not os.path.exists(pdbfile_path):
        logging.error(f"Could not find {pdbfile_path} file")
        raise ValueError(f"Could not find {pdbfile_path} file")
    residuenum, atomnum = get_res_atom_number(pdbfile_path)

    ethreshp = float(0.2 * atomnum + eptot)
    alphap = float(0.2 * atomnum)
    ethreshd = float(4.0 * residuenum + dihed)
    alphad = float(4.0 * residuenum * 0.2)

    make_amdin(
        ethreshp, alphap, ethreshd, alphad, nmropt, basedir, outdir, amdinputfile
    )
    make_runsh(basedir, indir, prerunfile, outdir, rstfile, amdrunfile)


# %%
flags.DEFINE_string("indir", None, "Path to input directory file.")
flags.DEFINE_string(
    "outdir", None, "Path to a directory that will store amd input files."
)
flags.DEFINE_string(
    "basedir",
    ".",
    "Base directory. Default is the current directory.",
)
flags.DEFINE_string(
    "topdir",
    "../../top",
    "The directory containing 'leap.parm7' and 'leap.pdb' files. Default is '../../top'.",
)
flags.DEFINE_string(
    "mdoutfile",
    "md.out",
    "The name of mdout file in the 'indir'. (Default is 'md.out')",
)
flags.DEFINE_string(
    "rstfile",
    "md.rst7",
    "The name of AMBER restart file in the 'indir'. (Default is 'md.rst7')",
)
flags.DEFINE_string(
    "pdbfile",
    "leap.pdb",
    "The name of leap PDB file in the 'topdir'. (Default is 'leap.pdb')",
)
flags.DEFINE_string(
    "amdinputfile", "amd.in", "amd input file that will be created in 'outdir'. "
)
flags.DEFINE_string(
    "amdrunfile", "run.sh", "amd run file that will be created in 'outdir'. "
)
flags.DEFINE_string(
    "prerunfile",
    "run.sh",
    "previos run file in 'indir'. Default is 'run.sh'.",
)
flags.DEFINE_integer(
    "nmropt",
    0,
    "Use NMR restraints or not. Deafult is '0'",
)


FLAGS = flags.FLAGS


def main(argv):
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    # main process: amd.inファイルを作り出す
    write_amdinputfile(
        FLAGS.basedir,
        FLAGS.indir,
        FLAGS.mdoutfile,
        FLAGS.outdir,
        FLAGS.amdinputfile,
        FLAGS.prerunfile,
        FLAGS.amdrunfile,
        FLAGS.topdir,
        FLAGS.pdbfile,
        FLAGS.rstfile,
        FLAGS.nmropt,
    )


if __name__ == "__main__":
    flags.mark_flags_as_required(
        [
            "indir",
            "outdir",
        ]
    )

    app.run(main)
