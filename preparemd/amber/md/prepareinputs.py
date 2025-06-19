import os
import shutil
import subprocess
import tempfile
import textwrap

from Bio.PDB.PDBParser import PDBParser
from loguru import logger

from preparemd.amber.md import heat, minimize, production
from preparemd.utils import header
from preparemd.utils.log import log_setup

log_setup(level="INFO")


def write_minimizeinput(
    dir: str, machineenv: str, minimizedir: str = "minimize"
) -> None:
    """make AMBER inputfiles for minimization"""
    if not os.path.exists(os.path.join(dir, minimizedir)):
        os.makedirs(os.path.join(dir, minimizedir))
    min1file = os.path.join(dir, minimizedir, "min1.in")
    min2file = os.path.join(dir, minimizedir, "min2.in")
    runfile = os.path.join(dir, minimizedir, "run.sh")

    with open(min1file, mode="w") as f:
        f.write(minimize.min1input())
    with open(min2file, mode="w") as f:
        f.write(minimize.min2input())
    with open(runfile, mode="w") as f:
        f.write(minimize.runinput(machineenv=machineenv))

    os.chmod(runfile, 0o755)


def write_heatinput(
    dir, residuenum: int, machineenv: str, heatdir: str = "heat"
) -> None:
    """make AMBER inputfiles for equilibration
    Args:
        dir: 出力先のディレクトリ名
        residuenum: 入力pdbファイルの残基数。
                    heatのときにposition restraintsをかける範囲指定のために必要。
        heatdir: 出力先のディレクトリ名で作るheatのインプットファイルを入れるディレクトリ名。
        初期値は"heat"
    """  # noqa: E501
    if not os.path.exists(os.path.join(dir, heatdir)):
        os.makedirs(os.path.join(dir, heatdir))
    # 徐々にrestraint_wtの値を小さくしていく
    weights = [10.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.0]
    for i in range(1, 10):
        # md1.inにはirest=0, ntx=1、md2-md9.inにはirest=1, ntx=5を指定する。
        is_md1 = True if i == 1 else False
        if is_md1:
            restart_input = textwrap.dedent(
                """irest=0,                        ! DO NOT restart MD simulation from a previous run.
                   ntx=1,                          ! Coordinates and velocities will not be read"""  # noqa: E501
            )
            simtime = 100000
            ntp = "ntp=0,                          ! No pressure scaling (Default)"
            ntb = "ntb=1,                          ! Constant Volume. NVT simulation."
            temperature = textwrap.dedent(
                """tempi=10.0,                     ! Initial Temperature. For the initial dynamics run, (NTX < 3) the velocities are assigned from a Maxwellian distribution at TEMPI K.tempi=10.0,                     ! Initial Temperature. For the initial dynamics run, (NTX < 3) the velocities are assigned from a Maxwellian distribution at TEMPI K.
                   temp0=300.0,                    ! Reference temperature at which the system is to be kept."""  # noqa: E501
            )
            annealing = textwrap.dedent(
                """\
                /
                &wt TYPE='TEMP0', istep1=0, istep2=100000,
                    value1=10.0, value2=300.0, /
                &wt TYPE='END'
                """
            )
        else:
            restart_input = textwrap.dedent(
                """irest=1,                        ! Restart MD simulation from a previous run.
                   ntx=5,                          ! Coordinates and velocities will be read from a previous run."""  # noqa: E501
            )
            simtime = 50000
            ntp = "ntp=1,                          ! MD simulations with isotropic position scaling"
            ntb = "ntb=2,                          ! Constant Pressure. NPT simulation."
            temperature = "temp0=300.0,                  ! Reference temperature at which the system is to be kept."  # noqa: E501
            annealing = textwrap.dedent(
                """\
                /
                &wt
                    type='DUMPFREQ', istep1=5000,
                /
                &wt type='END' /
                DISANG=dist1.rst
                DUMPAVE=dist1.dat
                """
            )

        md_i = heat.heatinput(
            restart_input,
            simtime,
            ntp,
            ntb,
            annealing,
            residuenum,
            weights,
            i,
            temperature,
        )
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
    # 各ディレクトリではns_per_mddirで指定した時間(ns)だけMDシミュレーションを
    # 実行するためのインプットファイルを作成する。
    for i in range(1, box + 1):
        # box_zeroはboxを桁数指定で0埋めしたもの
        box_zero = str(i).zfill(3)
        if not os.path.exists(os.path.join(dir, productiondir, box_zero)):
            os.makedirs(os.path.join(dir, productiondir, box_zero))

        # i == 1 ならばrestartしない。それ以外はrestartをONにする
        # 直前のMD runの速度情報を引き継ぐ
        do_restart = False if i == 1 else True
        if do_restart:
            restart_input = textwrap.dedent(
                """\
                irest=1,              ! Restart MD simulation from a previous run.
                ntx=5,                ! Coordinates and velocities will be read from a previous run."""  # noqa: E501
            )
        else:
            restart_input = textwrap.dedent(
                """\
                irest=0,              ! DO NOT restart MD simulation from a previous run.
                ntx=1,                ! Coordinates and velocities will not be read."""  # noqa: E501
            )
        mdinput = production.productioninput(restart_input, ns_per_mddir)
        mdfile = os.path.join(dir, productiondir, box_zero, "md.in")
        with open(mdfile, mode="w") as f:
            f.write(mdinput)

        runfile = os.path.join(dir, productiondir, box_zero, "run.sh")
        if i == 1:
            prevrstfile = "../../heat/md9.rst7"
        runinput = production.runinput(prevrstfile, machineenv=machineenv)
        with open(runfile, mode="w") as f:
            f.write(runinput)
        os.chmod(runfile, 0o755)

        prevrstfile = os.path.join("..", box_zero, "md.rst7")


def write_totalrunscript(dir: str, box: int, machineenv: str) -> None:
    """make a run.sh file to run"""
    totalrunfile = os.path.join(dir, "totalrun.sh")
    runinput = textwrap.dedent("""\
    {header}
    (
        cd minimize
        {minimize_content}
    ) || exit $?
    (
        cd heat
        {heat_content}
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
    """).format(
        header=header.queue_header(machineenv=machineenv),
        minimize_content=minimize.minimizercontent(),
        heat_content=heat.heatcontent(),
        box=box,
    )
    with open(totalrunfile, mode="w") as f:
        f.write(runinput)
    os.chmod(totalrunfile, 0o755)


def prepareamberfiles(
    distdir: str, residuenum: int, box: int, ns_per_mddir: int, machineenv: str
) -> None:
    """prepare AMBER input files for minimize, heat, and pr directories

    Args:
        distdir: 出力先のディレクトリ名。この中にamber, topディレクトリが作られることを想定する。
        residuenum: 系に存在する残基数。position restraintsをかける対象の原子の残基範囲と一致する。
        box: prディレクトリ内部に作成するサブディレクトリ数(001, 002, ...)。
        ns_per_mddir: 上記のサブディレクトリにつき、何nsのシミュレーションを行うか。
        machineenv: どこでMDを実行するか
    """
    outputdir = os.path.join(distdir, "amber")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    write_minimizeinput(outputdir, machineenv=machineenv)
    write_heatinput(outputdir, residuenum=residuenum, machineenv=machineenv)
    write_productioninput(
        outputdir, machineenv=machineenv, box=box, ns_per_mddir=ns_per_mddir
    )
    write_totalrunscript(outputdir, box=box, machineenv=machineenv)


def get_boxsize_from_pre2(pre2file: str):
    with open(pre2file) as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if "CRYST1" in line:
                line_ = line.split()
                boxsize = f"{line_[1]} {line_[2]} {line_[3]}"
                break
    return boxsize


def preparepre2file(distdir: str, rotate: str = "", sslink_file: str = ""):
    """prepare pre2.pdb file.
    translate pre.pdb file to center (0,0,0)."""

    cpptraj_path = shutil.which("cpptraj")
    if cpptraj_path is None:
        raise RuntimeError(
            "cpptraj command was not found. Make sure AmberTools was correctly installed."
        )

    pdbfile_path = os.path.join(distdir, "top", "pre.pdb")
    outfile_path = os.path.join(distdir, "top", "pre2.pdb")
    fp = tempfile.NamedTemporaryFile(suffix=".in", mode="w+t", encoding="utf-8")
    fp.write(
        textwrap.dedent(
            f"""parm {pdbfile_path}
        trajin {pdbfile_path}
        box auto
        autoimage @CA origin
        {rotate}
        trajout {outfile_path}
        go
        """
        )
    )
    fp.seek(0)
    cmd = [cpptraj_path, "-i", fp.name, "-o", "/dev/null"]

    logger.info(f"Launching subprocess {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stderr)
        raise RuntimeError("cpptraj process failed.")

    fp.close()

    boxsize = get_boxsize_from_pre2(outfile_path)

    # outfile_path中のCYX残基はすべてCYSにする
    with open(outfile_path, "rt") as f:
        x = f.read()

    with open(outfile_path, "wt") as f:
        x = x.replace("CYX", "CYS")
        f.write(x)

    return boxsize


def get_resultboxsize(logfile: str) -> list[str]:
    """Get Box size info from leap.log"""
    with open(logfile) as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        if "Total vdw box size" in line:
            line_ = line.replace("Total vdw box size:", "")
            line_ = line_.replace("angstroms.", "")
            result_boxsize_dict = line_.split()

    return result_boxsize_dict


def get_charge(logfile: str) -> list[str]:
    """Get Total perturbed charge info from leap.log"""
    with open(logfile) as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        if "Total perturbed charge" in line:
            line_ = line.replace("Total perturbed charge:", "")
            result_charge = line_.split()

    return result_charge


def run_leap(distdir: str, boxsize: str, pre2boxsize: str) -> None:
    """make leap.in file to run tleap command."""
    tleap_path = shutil.which("tleap")
    if tleap_path is None:
        raise RuntimeError(
            "tleap command was not found. Make sure AmberTools was correctly installed."
        )

    # 作業ディレクトリを一時的に変更
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, distdir, "top"))
    leapinfile = "leap.in"
    if not os.path.isfile(leapinfile):
        raise FileNotFoundError(f"{leapinfile} was not found.")
    outlogfile = "leap.log"
    if os.path.isfile(outlogfile):
        os.remove(outlogfile)
    cmd = [tleap_path, "-f", leapinfile]

    logger.info(f"Launching subprocess {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stdout.decode())
        print(stderr.decode())
        os.chdir(cwd)
        raise RuntimeError("tleap process failed.")

    # leap終了時のボックスサイズを取得
    result_boxsize = get_resultboxsize(outlogfile)
    if boxsize == "":
        inputsize = pre2boxsize.split()
    else:
        inputsize = boxsize.split()

    if not (
        float(result_boxsize[0]) - float(inputsize[0]) < 5.0
        and float(result_boxsize[1]) - float(inputsize[1]) < 5.0
        and float(result_boxsize[2]) - float(inputsize[2]) < 5.0
    ):
        print(f"Warning: Result box size is {result_boxsize}.")

    # 作業ディレクトリの変更終了
    os.chdir(cwd)


def cys_to_cyx_in_pre2file(distdir: str, sslink_file: str) -> None:
    """
    すでに一度CYX残基がCYSに修正されたpre2.pdbファイルについて、sslinkに応じて再度
    該当残基をCYX残基にする操作
    """
    pre2file = os.path.join(distdir, "top", "pre2.pdb")
    cyxresnums = []
    with open(sslink_file) as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            cyxresnums.append(int(line.split()[0]))
            cyxresnums.append(int(line.split()[1]))

    with open(pre2file, "rt") as f:
        lines = f.readlines()

    outcontent = []
    with open(pre2file, "wt") as f:
        for line in lines:
            if line.startswith("ATOM  "):
                resnum = int(line[22:26])
                if resnum in cyxresnums:
                    if line[17:20] != "CYS":
                        raise Exception(f"Residue {resnum} is not CYS residue.")
                    else:
                        line = line.replace("CYS", "CYX")
            outcontent.append(line)
        f.writelines(outcontent)


def run_pdb4amber(
    pdbfile_path: str, distdir: str, strip: str = "", sslink_file: str = ""
):
    """run pdb4amber command to obtain cleaned pdb and sslink files.
    pdb4amber is a command in AmberTools that prepares PDB files for MD simulations.
    It processes the input PDB file, removes unwanted residues or atoms, and generates
    a cleaned PDB file along with a file containing SS bond information.

    Args:
        pdbfile_path (str): input PDB file path to be processed by pdb4amber.
        distdir (str): output directory. A "top" directory will be created inside this directory.
        strip (str): residue numbers to be excluded from the MD simulation in the input PDB file.
                     This should be specified using AMBER MASK syntax.
                     For example, to delete residues 793-807 and 864-878 from the PDB file,
                     specify :793-807,864-878.
        sslink_file (str): SS bond information file.
                     This is the file that contains the SS bond information generated by pdb4amber.
                     If provided, the SS link information in that file will be used preferentially.

    Returns:
        resnum: pdb4amberを通して出てきた整形済みのpdbファイル。HIS->HIDまたはHIE, CYS -> CYXになっている
        sslink_file: pdb4amberを通して出てきたSS結合情報を格納したテキストファイル
    """
    pdb4amber_path = shutil.which("pdb4amber")
    if pdb4amber_path is None:
        raise RuntimeError(
            "pdb4amber command was not found. Make sure AmberTools was correctly installed."
        )

    if not os.path.exists(os.path.join(distdir, "top")):
        os.makedirs(os.path.join(distdir, "top"))
    outputfile = os.path.join(distdir, "top", "pre.pdb")
    # delete H, H2, H3 atoms in the N-terminus residue with `-s` option because `tleap` will fail.
    # This is a workaround for the issue that tleap does not handle H, H2, H3 atoms in the N-terminus residue.
    # CONECT records are not written to the output file.
    if strip != "":
        strip += " | @H, H2, H3, HG"
    else:
        strip = "@H, H2, H3, HG"
    cmd = [pdb4amber_path, "-i", pdbfile_path, "-o", outputfile, "-s", strip]

    logger.info(f"Launching subprocess {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stderr)
        raise RuntimeError("pdb4amber process failed.")

    if sslink_file == "":
        sslink_file = os.path.join(distdir, "top", "pre_sslink")

    if not os.path.isfile(sslink_file):
        raise FileNotFoundError(f"{sslink_file} file is not found.")

    # outputfile内に存在する残基数の情報がposition restraintsの生成に必要。
    pdb_parser = PDBParser(QUIET=True)
    struc = pdb_parser.get_structure("pre", outputfile)
    resnum = 0
    for model in struc:
        for chain in model:
            for r in chain.get_residues():
                if r.get_resname() != "WAT":
                    resnum += 1

    return resnum, sslink_file
