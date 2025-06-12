import textwrap

from preparemd.utils import header


def heatinput(
    restart_input: str,
    simtime: int,
    ntp: str,
    ntb: str,
    annealing: str,
    residuenum: int,
    weights: list,
    number: int,
    temperature: str,
) -> str:
    """Write md[1-9].in file. Do not use f-string here, use .format() instead."""
    heat_template = textwrap.dedent("""\
        Heat system (constant volume)
        &cntrl
            imin=0,                         ! Molecular Dynamics
            {restart_input}
            nstlim={simtime},               ! Number of MD steps ( 200 ps )
            dt=0.002,                       ! Timestep (ps)
            igb=0,                          ! No generalized Born term is used (Default)
            ntp=0,                          ! No pressure scaling (Default)
            {ntp}
            {ntb}
            ntc=2,                          ! SHAKE on for bonds involving hydrogen atoms
            ntf=2,                          ! No force evaluation for bonds with hydrogen
            cut=8.0,                        ! Nonbonded cutoff (Angstroms)
            iwrap=1,                        ! the coordinates written to the restart and trajectory files will be "wrapped" into a primary box.
            ntpr=5000,                      ! Print to mdout every ntpr steps
            ntwx=5000,                      ! Write to trajectory file every ntwx steps
            ntwr=5000,                      ! Every ntwr steps during dynamics, the "restrt" file will be written
            ntt=3,                         ! Langevin thermostat
            gamma_ln=2.0,                   ! Collision frequency for thermostat
            ig=-1,                         ! Random seed for Langevin thermostat
            {temperature}
            ntr=1,                         ! Harmonic position restraints ON
            restraintmask=':1-{residuenum} & !@H=',  ! Atoms to be restrained
            restraint_wt={restraint_weight},              ! Restraint weight
            ioutfm=1,                      ! Binary NetCDF trajectory
            nmropt=0,                      ! NMR restraints off
            {annealing}/
    """).format(
        restart_input=restart_input,
        simtime=simtime,
        ntp=ntp,
        ntb=ntb,
        temperature=temperature,
        residuenum=residuenum,
        restraint_weight=weights[number - 1],
        annealing=annealing,
    )
    return heat_template


def heatcontent() -> str:
    """process of heat/run.sh"""

    content = textwrap.dedent(
        """
topfile="../../top/leap.parm7"
prev_rst7="../minimize/min2.rst7"

for (( i=1;i<10;i++ ));do
    echo "Start the ${i} cycle."
    #まだmd${i}ステップが終わっていなければ(md${i}.rst7が存在していないなら)実行
    if [ ! -f md${i}.rst7 ];then
        pmemd.cuda_SPFP.MPI -O \\
            -i md${i}.in \\
            -o md${i}.out \\
            -p ${topfile} \\
            -c ${prev_rst7} \\
            -ref ${prev_rst7} \\
            -r md${i}.rst7 \\
            -x md${i}.nc \\
            -inf md${i}.info || exit $?
    #すでにmd${i}ステップが終わっていれば次のサイクルへ移動
    else
        echo "md${i}.rst7 exists. Starts next cycle."
    fi
    prev_rst7="md${i}.rst7"
done
# 不要であればmd1~md9.ncを消去
rm md[1-9].nc
# ambpdbでmd9.rst7をmd9.pdbファイルに変換
ambpdb -p ${topfile} -c md9.rst7 > md9.pdb
"""
    )
    return content


def runinput(machineenv: str) -> str:
    """content of heat/run.sh"""
    runinput = header.queue_header(machineenv=machineenv)
    runinput += heatcontent()
    return runinput
