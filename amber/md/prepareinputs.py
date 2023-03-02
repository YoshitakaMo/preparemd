import os
from amber.md import minimize
from amber.md import heat
from amber.md import production
from amber.md import header


def write_minimizeinput(
    dir: str, machineenv: str, minimizedir: str = "minimize"
) -> None:
    """make AMBER inputfiles for minimization"""
    if not os.path.exists(os.path.join(dir, minimizedir)):
        os.makedirs(os.path.join(dir, minimizedir))
    min1file = os.path.join(dir, minimizedir, "min1.in")
    min2file = os.path.join(dir, minimizedir, "min2.in")
    runfile = os.path.join(dir, minimizedir, "run.sh")

    min1input = minimize.min1input()
    min2input = minimize.min2input()
    runinput = minimize.runinput(machineenv=machineenv)

    with open(min1file, mode="w") as f:
        f.write(min1input)
    with open(min2file, mode="w") as f:
        f.write(min2input)
    with open(runfile, mode="w") as f:
        f.write(runinput)

    os.chmod(runfile, 0o755)


def write_heatinput(
    dir, residuenum: int, machineenv: str, heatdir: str = "heat"
) -> None:
    """make AMBER inputfiles for equilibration
    Args:
        dir: 出力先のディレクトリ名
        residuenum: 入力pdbファイルの残基数。heatのときにposition restraintsをかける範囲指定のために必要。
        heatdir: 出力先のディレクトリ名で作るheatのインプットファイルを入れるディレクトリ名。
        初期値は"heat"
    """
    if not os.path.exists(os.path.join(dir, heatdir)):
        os.makedirs(os.path.join(dir, heatdir))
    # 徐々にrestraint_wtの値を小さくしていく
    weights = [10.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.0]
    for i in range(1, 10):
        # md1.inにはirest=0, ntx=1、md2-md9.inにはirest=1, ntx=5を指定する。
        is_md1 = True if i == 1 else False
        if is_md1:
            restart_input = """irest=0,                        ! DO NOT restart MD simulation from a previous run.
    ntx=1,                          ! Coordinates and velocities will not be read"""
            simtime = 100000
            annealing = """ /
&wt TYPE='TEMP0', istep1=0, istep2=100000,
    value1=10.0, value2=300.0, /
&wt TYPE='END'
"""
        else:
            restart_input = """irest=1,                        ! Restart MD simulation from a previous run.
    ntx=5,                          ! Coordinates and velocities will be read from a previous run."""
            simtime = 50000
            annealing = """ /
&wt
    type='DUMPFREQ', istep1=5000,
/
&wt type='END' /
DISANG=dist1.rst
DUMPAVE=dist1.dat
"""

        md_i = heat.heatinput(restart_input, simtime, annealing, residuenum, weights, i)
        mdfile = os.path.join(dir, heatdir, f"md{i}.in")
        with open(mdfile, mode="w") as f:
            f.write(md_i)

        runfile = os.path.join(dir, heatdir, "run.sh")
        runinput = heat.runinput(machineenv=machineenv)
        with open(runfile, mode="w") as f:
            f.write(runinput)
        os.chmod(runfile, 0o755)


def write_productioninput(
    dir, machineenv: str, box: int = 3, ns_per_mddir: int = 50, productiondir="pr"
) -> None:
    """make AMBER input files for production run"""
    if not os.path.exists(os.path.join(dir, productiondir)):
        os.makedirs(os.path.join(dir, productiondir))
    mdfile = os.path.join(dir, productiondir, "md.in")

    # prディレクトリの中にboxで指定した数だけ001〜xxxというディレクトリを作成する
    # 各ディレクトリではns_per_mddirで指定した時間(ns)だけMDシミュレーションを実行するための
    # インプットファイルを作成する。
    for i in range(1, box + 1):
        # box_zeroはboxを桁数指定で0埋めしたもの
        box_zero = str(i).zfill(3)
        if not os.path.exists(os.path.join(dir, productiondir, box_zero)):
            os.makedirs(os.path.join(dir, productiondir, box_zero))

        # i == 1 ならばrestartしない。それ以外はrestartをONにする（＝直前のMD runの速度情報を引き継ぐ）
        do_restart = False if i == 1 else True
        if do_restart:
            restart_input = """irest=1,              ! Restart MD simulation from a previous run.
    ntx=5,                ! Coordinates and velocities will be read from a previous run."""
        else:
            restart_input = """irest=0,              ! DO NOT restart MD simulation from a previous run.
    ntx=1,                ! Coordinates and velocities will not be read."""
        mdinput = production.productioninput(restart_input, ns_per_mddir)
        mdfile = os.path.join(dir, productiondir, box_zero, "md.in")
        with open(mdfile, mode="w") as f:
            f.write(mdinput)

        runfile = os.path.join(dir, productiondir, box_zero, "run.sh")
        if i == 1:
            prevrstfile = "../../heat/md9.rst7"  # heat直後のrstファイル。
        runinput = production.runinput(prevrstfile, machineenv=machineenv)
        with open(runfile, mode="w") as f:
            f.write(runinput)
        os.chmod(runfile, 0o755)

        prevrstfile = os.path.join("..", box_zero, "md.rst7")


def write_totalrunfile(dir: str, box: int, machineenv: str) -> None:
    """make a run.sh file to run"""
    totalrunfile = os.path.join(dir, "totalrun.sh")
    runinput = header.qsubheader(machineenv=machineenv)
    runinput += "test ${PBS_NP} || PBS_NP=8\n"
    runinput += f"""
(
cd minimize
{minimize.minimizercontent()}
) || exit $?
(
cd heat
{heat.heatcontent()}
) || exit $?
topfile="../../../top/leap.parm7"
rstfile="../../heat/md9.rst7"
cd pr
for i in `seq 1 {box}`; do
    j=$(printf "%03d\\n" "${{i}}")
    cd $j
    pmemd.cuda_SPFP.MPI -O \\
        -i md.in \\
        -o md.out \\
        -p ${{topfile}} \\
        -c ${{rstfile}} \\
        -r md.rst7 \\
        -ref ${{topfile}} || exit $?
    rstfile="../${{j}}/md.rst7"
    cd ..
done
"""
    with open(totalrunfile, mode="w") as f:
        f.write(runinput)
    os.chmod(totalrunfile, 0o755)
