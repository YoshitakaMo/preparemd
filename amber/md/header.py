def qsubheader(ppn: int = 16) -> str:
    """Template file for run.sh to qsub.
    Please modify this file for your calculation environments."""

    qsub_template = f"""#!/bin/sh
#PBS -q default
#PBS -l nodes=1:ppn={ppn}:gpus=1
#PBS -l walltime=72:00:00

test $PBS_O_WORKDIR && cd $PBS_O_WORKDIR
# run the environment module
if test -f /home/apps/Modules/init/profile.sh; then
    . /home/apps/Modules/init/profile.sh
    module load amber22
elif test -f /usr/local/Modules/init/profile.sh; then
    . /usr/local/Modules/init/profile.sh
    module load amber22
fi
### Write your qsub script from here.
echo `hostname`
"""
    return qsub_template

