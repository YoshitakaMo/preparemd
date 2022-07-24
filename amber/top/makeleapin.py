import os
from amber.top import leapin

def makeleapin(dir: str,
               boxsize: str,
               pre2boxsize: str,
               ion_conc: float,
               sslink_file: str) -> None:
    """make a leap.in file"""
    if not os.path.exists(os.path.join(dir)):
        os.makedirs(os.path.join(dir))
    leapinfile = os.path.join(dir, "top", "leap.in")

    leapininput = leapin.leapininput(boxsize,
                                     pre2boxsize,
                                     ion_conc,
                                     sslink_file)

    with open(leapinfile, mode="w") as f:
        f.write(leapininput)
