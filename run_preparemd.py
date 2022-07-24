#%%
import os
import shutil
import subprocess
import tempfile
import Bio.PDB
from absl import logging
from absl import app
from absl import flags
from absl import logging
from amber.md import prepareinputs
from amber.md import writetrajfix
from amber.top import makeleapin

logging.set_verbosity(logging.INFO)

def run_pdb4amber(pdbfile_path: str , distdir: str, strip: str = "", sslink_file: str = ""):
    """run pdb4amber command to obtain cleaned pdb and sslink files

    Args:
        pdbfile_path: 入力とするpdbファイルのファイルパス
        distdir: 出力先のディレクトリ。この中にtopディレクトリを生成する。
        strip:  入力とするpdbファイルのうち、MDシミュレーションに含めない残基の番号。
                AMBER MASK文法で記述する。
                （例として、pdbファイルの最初から数えて793-807, 864-878番目の残基を削除するなら、
                 :793-807,864-878）
        sslink_file: SS結合のペア情報を格納したファイル。
                     pdb4amberで作られる"_sslink"と書かれているもの。
                     与えられた場合は、そのファイル内のsslink情報を優先して用いる。

    Returns:
        resnum: pdb4amberを通して出てきた整形済みのpdbファイル。HIS->HIDまたはHIE, CYS -> CYXになっている
        sslink_file: pdb4amberを通して出てきたSS結合情報を格納したテキストファイル
    """
    pdb4amber_path = shutil.which("pdb4amber")
    if pdb4amber_path is None:
        raise RuntimeError("pdb4amber command was not found. Make sure AmberTools was correctly installed.")

    if not os.path.exists(os.path.join(distdir, "top")):
        os.makedirs(os.path.join(distdir, "top"))
    outputfile = os.path.join(distdir, "top", "pre.pdb")
    # N末端にH, H2, H3原子が存在するとtleapのときにエラーになるので、-s @H, H2, @H3をつけてそれらを削除する
    # 出力ファイルにCONECTレコードを記載しない。
    if strip != "":
        strip += " | @H, H2, H3, HG"
    else:
        strip = '@H, H2, H3, HG'
    cmd = [
        pdb4amber_path,
        '-i', pdbfile_path,
        '-o', outputfile,
        '-s', strip]

    logging.info('Launching subprocess "%s"', ' '.join(cmd))
    process = subprocess.Popen(
    cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stderr)
        raise RuntimeError('pdb4amber process failed.')

    if sslink_file == "":
        sslink_file = os.path.join(distdir, "top", "pre_sslink")

    if not os.path.isfile(sslink_file):
        raise FileNotFoundError(f'{sslink_file} file is not found.')

    # outputfile内に存在する残基数の情報がposition restraintsの生成に必要。
    pdb_parser = Bio.PDB.PDBParser(QUIET = True)
    struc = pdb_parser.get_structure("pre", outputfile)
    resnum = 0
    for model in struc:
        for chain in model:
            for r in chain.get_residues():
                if r.get_resname() != "WAT":
                    resnum += 1

    return resnum, sslink_file


def prepareamberfiles(distdir: str,
                      residuenum: int,
                      box: int,
                      ns_per_mddir: int,
                      ppn: int = 16):
    """prepare AMBER input files for minimize, heat, and pr directories

    Args:
        distdir: 出力先のディレクトリ名。この中にamber, topディレクトリが作られることを想定する。

    Returns:
        inputpdb: pdb4amberを通して出てきた整形済みのpdbファイル。HIS->HID, HIEになっている
        sslink:   pdb4amberを通して出てきたSS結合情報を格納したテキストファイル
    """
    outputdir = os.path.join(distdir, "amber")
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    prepareinputs.write_minimizeinput(outputdir)
    prepareinputs.write_heatinput(outputdir, residuenum=residuenum)
    prepareinputs.write_productioninput(outputdir, box=box, ns_per_mddir=ns_per_mddir)
    prepareinputs.write_totalrunfile(outputdir, box=box, ppn=ppn)


def get_boxsize_from_pre2(pre2file: str):
    with open(pre2file) as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if "CRYST1" in line:
                line_ = line.split()
                boxsize = f"{line_[1]} {line_[2]} {line_[3]}"
                break
    return boxsize


def preparepre2file(distdir: str, rotate: str = "", sslink_file: str = "") -> None:
    """prepare pre2.pdb file.
    translate pre.pdb file to center (0,0,0)."""

    cpptraj_path = shutil.which("cpptraj")
    if cpptraj_path is None:
        raise RuntimeError("cpptraj command was not found. Make sure AmberTools was correctly installed.")

    pdbfile_path = os.path.join(distdir, "top", "pre.pdb")
    outfile_path = os.path.join(distdir, "top", "pre2.pdb")
    fp = tempfile.NamedTemporaryFile(suffix='.in',
                                     mode='w+t',
                                     encoding='utf-8')
    fp.write(f"""parm {pdbfile_path}
trajin {pdbfile_path}
autoimage origin
{rotate}
box auto
trajout {outfile_path}
go
""")
    fp.seek(0)
    cmd = [
        cpptraj_path,
        '-i', fp.name,
        '-o', "/dev/null"]

    logging.info('Launching subprocess "%s"', ' '.join(cmd))
    process = subprocess.Popen(
    cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stderr)
        raise RuntimeError('cpptraj process failed.')

    fp.close()

    boxsize = get_boxsize_from_pre2(outfile_path)

    # outfile_path中のCYX残基はすべてCYSにする
    with open(outfile_path, "rt") as f:
        x = f.read()

    with open(outfile_path, "wt") as f:
        x = x.replace("CYX","CYS")
        f.write(x)

    return boxsize

def get_resultboxsize(logfile: str) -> dict:
    """Get Box size info from leap.log"""
    with open(logfile) as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        if "Total vdw box size" in line:
            line_ = line.replace("Total vdw box size:", "")
            line_ = line_.replace("angstroms.", "")
            result_boxsize_dict = line_.split()

    return result_boxsize_dict


def get_charge(logfile: str) -> dict:
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
        raise RuntimeError("tleap command was not found. Make sure AmberTools was correctly installed.")

    # 作業ディレクトリを一時的に変更
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, distdir,"top"))
    leapinfile = "leap.in"
    if not os.path.isfile(leapinfile):
        raise FileNotFoundError(f"{leapinfile} was not found.")
    outlogfile = "leap.log"
    if os.path.isfile(outlogfile):
        os.remove(outlogfile)
    cmd = [tleap_path,
           '-f', leapinfile]

    logging.info('Launching subprocess "%s"', ' '.join(cmd))
    process = subprocess.Popen(
    cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    retcode = process.wait()

    if retcode:
        print(stdout.decode())
        print(stderr.decode())
        os.chdir(cwd)
        raise RuntimeError('tleap process failed.')

    # leap終了時のボックスサイズを取得
    result_boxsize = get_resultboxsize(outlogfile)
    if boxsize == "":
        inputsize = pre2boxsize.split()
    else:
        inputsize = boxsize.split()

    if not (float(result_boxsize[0]) - float(inputsize[0]) < 5.0 and
            float(result_boxsize[1]) - float(inputsize[1]) < 5.0 and
            float(result_boxsize[2]) - float(inputsize[2]) < 5.0):
        print(f"Warning: Result box size is {result_boxsize}.")

    # Perturbed Chargeの情報確認
    result_charge = get_charge(outlogfile)
    charge = float(result_charge[0])
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

#%%
flags.DEFINE_string('file', None, 'Path to input pdb file.')
flags.DEFINE_string('distdir', None, 'Path to a directory that will '
                    'store top and amber files.')
flags.DEFINE_string('strip', "",
                    'If provided, the specified region will be removed from '
                    'MD simulations. This is useful for signal peptides, for example.')
flags.DEFINE_integer('num_mddir', 3,
                     'Number of directories that will be made in the amber/pr directory. '
                     'Default is 3.')
flags.DEFINE_integer('ns_per_mddir', 50,
                     'Nanoseconds of MD simulations in each production run direcotry (amber/pr/001, 002, ...). '
                     'Default is 50 (ns).')
flags.DEFINE_integer('ion_conc', 150,
                     'Ion concentration in the periodic boudnary box of MD simulations. '
                     'Default is 150 (mM).')
flags.DEFINE_string('boxsize', "",
                    'The periodic boundary box for MD simulations will be this value, if provided. '
                    'For example, "120 120 120" will be a cube box with 120 Å on a side.'
                    'If no value is specified, the box size is automatically assigned '
                    'with 10 Å margins in the x, y, and z directions.')
flags.DEFINE_string('rotate', "", 'rotate the solute. '
                    'For example, "x 90" will rotate the solute 90 degrees around the x-axis.')
flags.DEFINE_string('sslink', "", 'input ssilnk file. e.g. "pre_sslink"'
                    'This file format is the same as an output sslink file of pdb4amber. '
                    'Set this value if you have a correct pair SS-bond list.')
flags.DEFINE_integer('ppn', 16, "number of cpus to calculate.")
flags.DEFINE_boolean('run_leap', True, 'Whether to run the leap process. '
                     'Turning leap process off may be useful to prepare only amber MD files.')

FLAGS = flags.FLAGS

def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    if FLAGS.num_mddir < 1:
        raise ValueError(f"The num_mddir argument must be 1 or more.")
    if FLAGS.ns_per_mddir < 1:
        raise ValueError(f"The ns_per_mddir argument must be 1 or more.")
    if FLAGS.ion_conc < 1:
        raise ValueError(f"The ion_conc argument must be 1 or more.")

    resnumber, sslink_file = run_pdb4amber(FLAGS.file,
                                      FLAGS.distdir,
                                      strip=FLAGS.strip,
                                      sslink_file=FLAGS.sslink)
    pre2boxsize = preparepre2file(FLAGS.distdir,
                                  rotate=FLAGS.rotate,
                                  sslink_file=sslink_file)
    cys_to_cyx_in_pre2file(FLAGS.distdir,
                           sslink_file=sslink_file)
    makeleapin.makeleapin(FLAGS.distdir,
                          boxsize=FLAGS.boxsize,
                          pre2boxsize=pre2boxsize,
                          ion_conc=FLAGS.ion_conc,
                          sslink_file=sslink_file)
    if FLAGS.run_leap:
        run_leap(FLAGS.distdir, FLAGS.boxsize, pre2boxsize)
    prepareamberfiles(FLAGS.distdir, resnumber, FLAGS.num_mddir, FLAGS.ns_per_mddir)
    writetrajfix.writetrajfix(FLAGS.distdir, resnumber, FLAGS.num_mddir)

if __name__ == '__main__':
    flags.mark_flags_as_required([
        'file',
        'distdir',
    ])

    app.run(main)

# 以下テスト用コード
# #%%
# file = "./ranked_0.pdb"
# distdir = "rank0"
# strip = ":793-807,864-878"
# num_mddir = 4
# ns_per_mddir = 30
# ion_conc = 150
# boxsize = "120 120 120"
# rotate = ""
# sslink = "./rank1/top/pre_sslink"
# ppn = 16
# #%%
# resnumber, sslink_file = run_pdb4amber(file,
#                                        distdir,
#                                        strip=strip,
#                                        sslink_file=sslink)
# pre2boxsize = preparepre2file(distdir,
#                               rotate=rotate,
#                               sslink_file=sslink_file)
# cys_to_cyx_in_pre2file(distdir, sslink_file=sslink_file)
# makeleapin.makeleapin(distdir,
#                       boxsize=boxsize,
#                       pre2boxsize=pre2boxsize,
#                       ion_conc=ion_conc,
#                       sslink_file=sslink_file)
# run_leap(distdir, boxsize, pre2boxsize)
# prepareamberfiles(distdir, resnumber, num_mddir, ns_per_mddir, ppn)
#%%

