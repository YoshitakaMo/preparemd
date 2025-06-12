from preparemd.amber.md.minimize import min1input, min2input


def test_min1input():
    expected_output = (
        "molecular dynamics minimization run 1\n"
        "&cntrl\n"
        "    imin=1,            ! Do Minimization\n"
        "    nmropt=0,          ! No restraints\n"
        "    ntx=1,             ! Coordinates, but no velocities, will be read (default)\n"
        "    irest=0,           ! Do NOT restart the simulation\n"
        "    ntxo=1,            ! ASCII Output Format of the final coordinates\n"
        "    ntpr=20,           ! Every ntpr steps, energy information will be printed.\n"
        "    ntwr=2000,         ! Every ntwr steps during dynamics, the “restrt” file will be written\n"
        "    ntwx=0,            ! Every ntwx steps, the coordinates will be written to the mdcrd file. if 0, no output.\n"
        "    ioutfm=0,          ! ASCII format of coordinate and velocity trajectory files (mdcrd, mdvel and inptraj).\n"
        "    ibelly=1,          ! If ibelly=1, the coordinates except the bellymasked atoms will be frozen.\n"
        '    bellymask=":WAT,Na+,Cl-",   ! mask for ibelly = 1\n'
        "    ntr=0,             ! Flag for restraining specified atoms in Cartesian space using a harmonic potential. No restraints.\n"
        "    ntmin=1,           ! Method of minimization. For NCYC cycles the steepest descent method is used then conjugate gradient is switched on\n"
        "    maxcyc=200,        ! The maximum number of cycles of minimization. Default = 1.\n"
        '    ncyc=100,          ! If "ntmin" is 1, the method of minimization will be switched from steepest descent to conjugate gradient after NCYC cycles. Default 10.\n'
        "    nstlim=2000,       ! number of MD-steps to be performed.\n"
        "    nscm=0,            ! Flag for the removal of translational and rotational center-of-mass\n"
        "    jfastw=0,\n"
        "/\n"
    )

    assert min1input() == expected_output


def test_min2input():
    expected_output = (
        "molecular dynamics minimization run 2\n"
        "&cntrl\n"
        "    imin=1,            ! Do Minimization\n"
        "    nmropt=0,          ! No restraints\n"
        "    ntx=1,             ! Coordinates, but no velocities, will be read (default)\n"
        "    irest=0,           ! Do NOT restart the simulation\n"
        "    ntxo=1,            ! ASCII Output Format of the final coordinates\n"
        "    ntpr=20,           ! Every ntpr steps, energy information will be printed.\n"
        "    ntwr=2000,         ! Every ntwr steps during dynamics, the “restrt” file will be written\n"
        "    ntwx=0,            ! Every ntwx steps, the coordinates will be written to the mdcrd file. if 0, no output.\n"
        "    ioutfm=0,          ! ASCII format of coordinate and velocity trajectory files (mdcrd, mdvel and inptraj).\n"
        "    ntr=0,             ! Flag for restraining specified atoms in Cartesian space using a harmonic potential. No restraints.\n"
        "    ntmin=1,           ! Method of minimization. For NCYC cycles the steepest descent method is used then conjugate gradient is switched on\n"
        "    maxcyc=200,        ! The maximum number of cycles of minimization. Default = 1.\n"
        '    ncyc=100,          ! If "ntmin" is 1, the method of minimization will be switched from steepest descent to conjugate gradient after NCYC cycles. Default 10.\n'
        "    nstlim=2000,       ! number of MD-steps to be performed.\n"
        "    nscm=0,            ! Flag for the removal of translational and rotational center-of-mass\n"
        "    jfastw=0,\n"
        "/\n"
    )

    assert min2input() == expected_output
