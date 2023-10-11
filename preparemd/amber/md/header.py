def pbsheader(machineenv: str = "yayoi") -> str:
    """Switch PBS header properly"""
    if machineenv == "wisteria":
        pbsheader = """#!/bin/bash -l
#PJM -g gw43
#PJM -L rscgrp=share,gpu=1,elapse=48:00:00
#PJM -j
# move to working directory
test $PJM_O_WORKDIR && cd $PJM_O_WORKDIR
module use -a /work/gw43/share/modulefiles
module load amber22
"""
    elif machineenv == "flow":
        pbsheader = """#!/bin/bash
#PJM -L rscunit=cx
#PJM -L rscgrp=cx-share
#PJM -L gpu=1
#PJM -L elapse=72:00:00
#PJM -j
# move to working directory
test $PJM_O_WORKDIR && cd $PJM_O_WORKDIR

. /usr/share/Modules/init/sh
module use -a /data/group1/z44243z/modulefiles
module load amber22
"""
    elif machineenv == "yayoi":
        pbsheader = """#!/bin/bash
#PBS -q default
#PBS -l nodes=1:ppn=16:gpus=1
#PBS -l walltime=72:00:00

test $PBS_O_WORKDIR && cd $PBS_O_WORKDIR
# run the environment module
if test -f /home/apps/Modules/init/profile.sh; then
    . /home/apps/Modules/init/profile.sh
    module load amber22
elif test -f /usr/local/Modules/init/profile.sh; then
    . /usr/local/Modules/init/profile.sh
    module load amber22
elif test -f /usr/share/Modules/init/profile.sh; then
    . /usr/share/Modules/init/profile.sh
    module load amber22
fi
"""
    elif machineenv == "brillantegw3":
        pbsheader = """#!/bin/bash
#PBS -q default
#PBS -l nodes=1:ppn=24:gpus=1
#PBS -l walltime=72:00:00

test $PBS_O_WORKDIR && cd $PBS_O_WORKDIR
# run the environment module
if test -f /home/apps/Modules/init/profile.sh; then
    . /home/apps/Modules/init/profile.sh
    module load amber22
elif test -f /usr/local/Modules/init/profile.sh; then
    . /usr/local/Modules/init/profile.sh
    module load amber22
elif test -f /usr/share/Modules/init/profile.sh; then
    . /usr/share/Modules/init/profile.sh
    module load amber22
fi
"""

    return pbsheader


def qsubheader(machineenv: str) -> str:
    """Template file for run.sh to qsub.
    Please modify this file for your calculation environments."""

    qsub_template = f"""{pbsheader(machineenv = machineenv)}
### Write your qsub script from here.
echo `hostname`
"""
    return qsub_template
