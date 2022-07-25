import os

def writetrajfix(distdir: str, resnumber: int, num_mddir: int) -> None:
    """Write trajfix.in file in amber/pr directory."""

    trajfixfile = os.path.join(distdir, "amber", "pr", "trajfix.in")
    STEP = 50
    trajinpart = ""
    for i in range(1, num_mddir+1):
        # box_zeroはboxを桁数指定で0埋めしたもの
        box_zero = str(i).zfill(3)
        trajinpart += f"trajin {box_zero}/mdcrd 1 last {STEP}\n"

    trajfix_content = f"""## 1段階目のtrajin処理。
trajin 001/mdcrd 1 1 1
reference ../../top/leap.rst7
unwrap :1-{resnumber}
center :1-{resnumber}@CA mass origin
rms first out rmsd.dat @CA
strip :SOD,WAT,TIP3,Cl-,Na+
trajout init.pdb pdb nobox
go

clear trajin

## 2段階目のtrajin処理。
{trajinpart}
unwrap :1-{resnumber}
center :1-{resnumber}@CA mass origin
rms first out rmsd.dat @CA
strip :SOD,WAT,TIP3,Cl-,Na+

trajout comp.trr
go
"""
    with open(trajfixfile, mode="w") as f:
        f.write(trajfixfile)


