import textwrap


def queue_header(machineenv: str) -> str:
    """Switch queue_ header properly"""
    if machineenv == "flow":
        queue_header = textwrap.dedent(
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
            echo `hostname`
            """
        )
    elif machineenv == "yayoi":
        queue_header = textwrap.dedent(
            """\
            #!/bin/bash
            #queue_ -q default
            #queue_ -l nodes=1:ppn=16:gpus=1
            #queue_ -l walltime=72:00:00

            test $queue__O_WORKDIR && cd $queue__O_WORKDIR
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
            echo `hostname`
            """
        )
    elif machineenv == "foodin":
        queue_header = textwrap.dedent(
            """\
            #!/bin/bash
            #SBATCH -p q1
            #SBATCH -n 16
            #SBATCH --gpus 1
            #SBATCH -o %x.%j.out
            #SBATCH -e %x.%j.err

            # run the environment module
            . /home/apps/Modules/init/profile.sh
            module load amber24
            echo `hostname`
            """
        )

    return queue_header
