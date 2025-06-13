from preparemd.utils.header import queue_header


def test_queue_header():
    expected_output_flow = (
        "#!/bin/bash\n"
        "#PJM -L rscunit=cx\n"
        "#PJM -L rscgrp=cx-share\n"
        "#PJM -L gpu=1\n"
        "#PJM -L elapse=72:00:00\n"
        "#PJM -j\n"
        "# move to working directory\n"
        "test $PJM_O_WORKDIR && cd $PJM_O_WORKDIR\n"
        "\n"
        ". /usr/share/Modules/init/sh\n"
        "module use -a /data/group1/z44243z/modulefiles\n"
        "module load amber24"
    )
    assert queue_header("flow") == expected_output_flow

    expected_output_yayoi = (
        "#!/bin/bash\n"
        "#queue_ -q default\n"
        "#queue_ -l nodes=1:ppn=16:gpus=1\n"
        "#queue_ -l walltime=72:00:00\n"
        "\n"
        "test $queue__O_WORKDIR && cd $queue__O_WORKDIR\n"
        "# run the environment module\n"
        "if test -f /home/apps/Modules/init/profile.sh; then\n"
        "    . /home/apps/Modules/init/profile.sh\n"
        "    module load amber24\n"
        "elif test -f /usr/local/Modules/init/profile.sh; then\n"
        "    . /usr/local/Modules/init/profile.sh\n"
        "    module load amber24\n"
        "elif test -f /usr/share/Modules/init/profile.sh; then\n"
        "    . /usr/share/Modules/init/profile.sh\n"
        "    module load amber24\n"
        "fi"
    )
    assert queue_header("yayoi") == expected_output_yayoi

    expected_output = (
        "#!/bin/bash\n"
        "#SBATCH -p q1\n"
        "#SBATCH -n 16\n"
        "#SBATCH --gpus 1\n"
        "#SBATCH -o %x.%j.out\n"
        "#SBATCH -e %x.%j.err\n"
        "\n"
        "# run the environment module\n"
        ". /home/apps/Modules/init/profile.sh\n"
        "module load amber24"
    )
    assert queue_header("foodin") == expected_output
