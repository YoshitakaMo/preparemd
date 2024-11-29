import textwrap


def pbsheader(machineenv: str = "yayoi") -> str:
    """Switch PBS header properly"""
    if machineenv == "flow":
        pbsheader = textwrap.dedent(
            """\
            #!/bin/bash
            #PJM -L rscunit=cx
            #PJM -L rscgrp=cx-share
            #PJM -L gpu=1
            #PJM -L elapse=72:00:00
            #PJM -j
            # move to working directory
            test $PJM_O_WORKDIR && cd $PJM_O_WORKDIR

            . /usr/share/Modules/init/sh
            module use -a /data/group1/z44243z/modulefiles
            module load amber24
            """
        ).strip()
    elif machineenv == "yayoi":
        pbsheader = textwrap.dedent(
            """\
            #!/bin/bash
            #PBS -q default
            #PBS -l nodes=1:ppn=16:gpus=1
            #PBS -l walltime=72:00:00

            test $PBS_O_WORKDIR && cd $PBS_O_WORKDIR
            # run the environment module
            if test -f /home/apps/Modules/init/profile.sh; then
                . /home/apps/Modules/init/profile.sh
                module load amber24
            elif test -f /usr/local/Modules/init/profile.sh; then
                . /usr/local/Modules/init/profile.sh
                module load amber24
            elif test -f /usr/share/Modules/init/profile.sh; then
                . /usr/share/Modules/init/profile.sh
                module load amber24
            fi
            """
        ).strip()
    elif machineenv == "foodin":
        pbsheader = textwrap.dedent(
            """\
            #!/bin/bash
            #SBATCH -p all_q
            #SBATCH -n 32
            #SBATCH --gpus 1
            #SBATCH -o %x.%j.out
            #SBATCH -e %x.%j.err

            # run the environment module
            . /home/apps/Modules/init/profile.sh
            module load amber24
            """
        ).strip()

    return pbsheader


def qsubheader(machineenv: str) -> str:
    """Template file for run.sh to qsub.
    Please modify this file for your calculation environments."""

    qsub_template = textwrap.dedent(
        f"""{pbsheader(machineenv)}
        ### Write your qsub script from here.
        echo `hostname`
        """
    )
    return qsub_template
