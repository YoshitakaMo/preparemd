import os
import re
from absl import logging


def boxsize_checker(boxsize: str) -> str:
    """boxsizeの引数が''以外で与えられた場合に、boxsizeの値がスペース区切りの
    3つ組で、かついずれも0より大きい値になっていることを
    チェックするための関数"""
    if boxsize != "":
        boxsize_dict = boxsize.split()
        if len(boxsize_dict) != 3:
            raise ValueError("boxsize must be 3-tuple int/float values.")
        if not (
            is_plusnum(boxsize_dict[0])
            and is_plusnum(boxsize_dict[1])
            and is_plusnum(boxsize_dict[2])
        ):
            raise ValueError("Each boxsize element must be more than 0.")
    return boxsize


def is_plusnum(s) -> bool:
    """sに入った値が数値に変換可能で、かつ0よりも大きい値になっているかを返す関数"""
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True if float(s) > 0.0 else False


def calculate_ion_nums(boxsize: str, ion_conc: float) -> float:
    """Determine how many ions are needed in the system.
    Args:
        boxsize:  系のボックスサイズ。"x y z"のような3-tuple型かつ
                  いずれも0より大きい。
        ion_conc: イオン濃度。

    Returns:
        ionnum:   系に含めるべきイオンの個数
    """
    # https://ambermd.org/tutorials/basic/tutorial8/index.php
    # 120 * 120 * 120 のサイズのときに156.0個のイオンになれば良い

    # boxsizeはすでに3-tupleであることが保証されている前提
    boxsize = boxsize_checker(boxsize)
    box_dict = [float(x.strip()) for x in boxsize.split()]
    boxvolume = box_dict[0] * box_dict[1] * box_dict[2]
    ionnum = boxvolume * 0.0602 * ion_conc // 100000  # 切り捨て
    return int(ionnum)


def additional_params(frcmod: list, prep: list, mol2: list) -> str:
    """FLAGSで得た追加のパラメータパスをleap.inにまとめて書き下す
    loadAmberParams frcmod.Acetyl_CoA
    loadAmberPrep DON.prep
    ACA = loadMol2 Acetyl_CoA.mol2
    のような形で書き下す。
    入力はすべてリスト型（各要素はstring型）で取る。
    Args:
        frcmod: list, prep: list, mol2: list
    Returns:
        params: str
    """
    params = ""
    if frcmod is not None:
        for i in frcmod:
            file = os.path.split(i)[1]
            if not os.path.exists(file):
                logging.error(f"Could not find frcmod file, {file}")
                raise ValueError(f"Could not find frcmod file, {file}")

            params += f"loadAmberParams {file}\n"
    if prep is not None:
        for i in prep:
            file = os.path.split(i)[1]
            if not os.path.exists(file):
                logging.error(f"Could not find prep file, {file}")
                raise ValueError(f"Could not find prep file, {file}")
            params += f"loadAmberPrep {file}\n"
    if mol2 is not None:
        for i in mol2:
            # iは'ACA = loadMol2 Acetyl_CoA.mol2', 'DON = loadMol2 DON.mol2'のような形式
            # 'loadMol2'の後のファイルパスを修正し、distdirディレクトリ内のものを使用するようにする
            # objnameに'ACA'が入るようにする
            objname = [a for a in re.split("=| |loadMol2", i) if a != ""][0]
            filepath = [a for a in re.split("=| |loadMol2", i) if a != ""][1]
            params += f"{objname} = loadMol2 {filepath}\n"

    return params


def get_sspair_from_sslink_file(sslink_file) -> dict:
    """sslink_fileから結合情報をleap.inに書き出す。
    例として
    bond mol.262.SG mol.274.SG
    bond mol.268.SG mol.282.SG"""
    sspairlist = []
    with open(sslink_file) as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            sspairlist.append([line.split()[0], line.split()[1]])

    ssbondinfo = ""
    for sspair in sspairlist:
        ssbondinfo += f"bond mol.{sspair[0]}.SG mol.{sspair[1]}.SG\n"

    return ssbondinfo


def leapininput(
    boxsize: str,
    pre2boxsize: str,
    ion_conc: float,
    sslink_file: str,
    fftype: str,
    frcmod: list,
    prep: list,
    mol2: list,
) -> str:
    """Content of leap.in file"""
    boxsize = boxsize_checker(boxsize)
    pre2boxsize = boxsize_checker(pre2boxsize)

    if boxsize == "":
        boxsize = pre2boxsize
        boxmargin = 10
    else:
        boxmargin = 0.01

    # イオンの個数はボックスサイズで決まる
    ionnum = calculate_ion_nums(boxsize=boxsize, ion_conc=ion_conc)

    ssbondinfo = get_sspair_from_sslink_file(sslink_file)

    if fftype == "ff14SB":
        prot_wat_forcefield = """#AMBER の力場パラメータff14SBを読み込む
source leaprc.protein.ff14SB
source leaprc.water.tip3p
source leaprc.gaff2

#追加のイオンの力場の導入
loadAmberParams frcmod.ionsjc_tip3p"""
    elif fftype == "ff19SB":
        prot_wat_forcefield = """#AMBER の力場パラメータff19SBとOPC力場を読み込む
source leaprc.protein.ff19SB
source leaprc.water.opc
source leaprc.gaff2

#ff19SBはOPC水モデルと組み合わせる。TIP3P水モデルとは組み合わせてはならない
loadAmberParams frcmod.opc"""

    additionalparams = additional_params(frcmod, prep, mol2)

    leapin_template = f"""{prot_wat_forcefield}
{additionalparams}

#pdbを"mol"として読み込む
mol = loadPDB pre2.pdb
{ssbondinfo}
center mol

#boxsize引数で指定された周期境界のボックスを形成する。
set mol box {{ {boxsize} }}

#イオンの追加・末尾の0は中和する数だけイオンを入れるという設定。
addIons2 mol Na+ {ionnum}
addIons2 mol Cl- 0

#ボックスの周りに更に{boxmargin}Aのボックスを設置し、溶媒和させる。
solvateBox mol TIP3PBOX {boxmargin}
#最後に、"mol"という溶媒和ボックスの系の電荷情報を表示する。0.00000になっていることが理想。
charge mol

#溶媒和された系のトポロジー・初期座標をleap.parm7, leap.rst7としてそれぞれ保存
saveAmberParm mol leap.parm7 leap.rst7

#溶媒和された系のPDBファイルをleap.pdbとして保存
savePDB mol leap.pdb
quit
"""
    return leapin_template
