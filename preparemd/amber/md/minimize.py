import textwrap

from preparemd.amber.md import header


def min1input() -> str:
    """Template file for min1.in"""

    min1_template = textwrap.dedent(
        """molecular dynamics minimization run 1
        &cntrl
            imin=1,            ! Do Minimization
            nmropt=0,          ! No restraints
            ntx=1,             ! Coordinates, but no velocities, will be read (default)
            irest=0,           ! Do NOT restart the simulation
            ntxo=1,            ! ASCII Output Format of the final coordinates
            ntpr=20,           ! Every ntpr steps, energy information will be printed.
            ntwr=2000,         ! Every ntwr steps during dynamics, the “restrt” file will be written
            ntwx=0,            ! Every ntwx steps, the coordinates will be written to the mdcrd file. if 0, no output.
            ioutfm=0,          ! ASCII format of coordinate and velocity trajectory files (mdcrd, mdvel and inptraj).
            ibelly=1,          ! If ibelly=1, the coordinates except the bellymasked atoms will be frozen.
            bellymask=":WAT,Na+,Cl-",   ! mask for ibelly = 1
            ntr=0,             ! Flag for restraining specified atoms in Cartesian space using a harmonic potential. No restraints.
            ntmin=1,           ! Method of minimization. For NCYC cycles the steepest descent method is used then conjugate gradient is switched on
            maxcyc=200,        ! The maximum number of cycles of minimization. Default = 1.
            ncyc=100,          ! If "ntmin" is 1, the method of minimization will be switched from steepest descent to conjugate gradient after NCYC cycles. Default 10.
            nstlim=2000,       ! number of MD-steps to be performed.
            nscm=0,            ! Flag for the removal of translational and rotational center-of-mass
            jfastw=0,
        /
        """  # noqa: E501
    )

    return min1_template


def min2input() -> str:
    """Template file for min2.in"""

    min2_template = textwrap.dedent(
        """molecular dynamics minimization run 2
        &cntrl
            imin=1,            ! Do Minimization
            nmropt=0,          ! No restraints
            ntx=1,             ! Coordinates, but no velocities, will be read (default)
            irest=0,           ! Do NOT restart the simulation
            ntxo=1,            ! ASCII Output Format of the final coordinates
            ntpr=20,           ! Every ntpr steps, energy information will be printed.
            ntwr=2000,         ! Every ntwr steps during dynamics, the “restrt” file will be written
            ntwx=0,            ! Every ntwx steps, the coordinates will be written to the mdcrd file. if 0, no output.
            ioutfm=0,          ! ASCII format of coordinate and velocity trajectory files (mdcrd, mdvel and inptraj).
            ntr=0,             ! Flag for restraining specified atoms in Cartesian space using a harmonic potential. No restraints.
            ntmin=1,           ! Method of minimization. For NCYC cycles the steepest descent method is used then conjugate gradient is switched on
            maxcyc=200,        ! The maximum number of cycles of minimization. Default = 1.
            ncyc=100,          ! If "ntmin" is 1, the method of minimization will be switched from steepest descent to conjugate gradient after NCYC cycles. Default 10.
            nstlim=2000,       ! number of MD-steps to be performed.
            nscm=0,            ! Flag for the removal of translational and rotational center-of-mass
            jfastw=0,
        /
        """  # noqa: E501
    )

    return min2_template


def minimizercontent() -> str:
    """process of minimize/run.sh"""
    content = textwrap.dedent(
        """DO_PARALLEL="mpirun -np ${PBS_NP} --mca orte_base_help_aggregate 0"
topfile="../../top/leap.parm7"
rstfile="../../top/leap.rst7"

if [ ! -f min2.rst7 ];then
    ${DO_PARALLEL} pmemd.MPI -O \\
        -i min1.in \\
        -o min1.out \\
        -p ${topfile} \\
        -c ${rstfile} \\
        -r min1.rst7 \\
        -inf min1.info || exit $?
    ${DO_PARALLEL} pmemd.MPI -O \\
        -i min2.in \\
        -o min2.out \\
        -p ${topfile} \\
        -c min1.rst7 \\
        -r min2.rst7 \\
        -inf min2.info || exit $?
else
    echo "min2.rst7 exists. Starts next cycle."
fi

if [ ! -f min2.pdb ];then
    # ambpdbコマンドでmin2操作後の座標ファイルをpdb形式のファイルに変換する
    ambpdb -p ${topfile} -c min2.rst7 > min2.pdb
fi
"""
    )  # noqa: E501
    return content


def runinput(machineenv: str) -> str:
    """content of minimize/run.sh"""

    runinput = header.qsubheader(machineenv=machineenv)
    runinput += "test ${PBS_NP} || PBS_NP=8\n"
    runinput += minimizercontent()

    return runinput
