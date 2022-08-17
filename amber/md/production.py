from amber.md import header


def productioninput(restart_input: str, box: int, ns_per_box: int) -> str:
    # simulation timeはns_per_box(ns)になるように指定
    simulationtime = ns_per_box * 500000

    """Template file for md[1-9].in"""
    prod_template = f"""vt-continue
&cntrl
    imin=0,               ! Molecular dynamics
    {restart_input}
    dt=0.002,             ! Timestep (ps)
    nstlim={simulationtime},      ! Number of MD steps
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
    nmropt=0,             ! turn on NMR restraints
/
&wt
    type='DUMPFREQ', istep1=5000,
/
&wt type='END' /
DISANG=dist1.rst
DUMPAVE=dist1.dat

"""

    return prod_template


def runinput(prevrstfile: str, ppn: int = 16) -> str:
    """Template file for pr/00x/run.sh"""

    qsub_template = header.qsubheader(ppn=ppn)
    run_template = (
        qsub_template
        + f"""
# トポロジーファイルの指定
topfile="../../../top/leap.parm7"
# 再開させたいrst7ファイルを指定
rstfile="{prevrstfile}"

pmemd.cuda_SPFP.MPI -O \\
    -i md.in \\
    -o md.out \\
    -p ${{topfile}} \\
    -c ${{rstfile}} \\
    -r md.rst7 \\
    -ref ${{topfile}}

"""
    )

    return run_template
