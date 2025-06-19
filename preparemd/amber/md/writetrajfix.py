import os
import textwrap


def writetrajfix(
    distdir: str, resnumber: int, num_mddir: int, suffix: str = ""
) -> None:
    """Write trajfix.in file in amber/pr directory.

    Args:
        distdir: 出力先のディレクトリ名。この中にamber, topディレクトリが作られる
                 ことを想定する。
        resnumber: 系に存在する残基数。position restraintsをかける対象の原子の
                   残基範囲と一致する。
        num_mddir: 上記のサブディレクトリにつき、何nsのシミュレーションを行うか。
        suffix: 出力トラジェクトリにつけるサフィックス。デフォルトは""。
    """

    trajfixfile = os.path.join(distdir, "amber", "pr", "trajfix.in")
    STEP = 50
    trajinpart = ""
    for i in range(1, num_mddir + 1):
        # box_zeroはboxを桁数指定で0埋めしたもの
        box_zero = str(i).zfill(3)
        trajinpart += f"trajin {box_zero}/mdcrd 1 last {STEP}\n"

    trajfix_content = textwrap.dedent(
        """\
            ## 1段階目のtrajin処理。
            trajin 001/mdcrd 1 1 1
            reference ../../top/leap.rst7
            unwrap :1-{resnumber}
            center :1-{resnumber}@CA mass origin
            rms first out rmsd.dat @CA
            strip :SOD,WAT,TIP3,Cl-,Na+
            trajout {suffix}init.pdb pdb nobox
            go

            clear trajin

            ## 2段階目のtrajin処理。
            {trajinpart}
            unwrap :1-{resnumber}
            center :1-{resnumber}@CA mass origin
            rms first out rmsd.dat @CA
            strip :SOD,WAT,TIP3,Cl-,Na+

            trajout {suffix}traj.trr
            go
        """
    ).format(resnumber=resnumber, suffix=suffix, trajinpart=trajinpart)
    with open(trajfixfile, mode="w") as f:
        f.write(trajfix_content)
