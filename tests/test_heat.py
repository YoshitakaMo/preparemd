from preparemd.amber.md.header import pbsheader
from preparemd.amber.md.heat import heatinput

restart_input = "irest=0, ntx=1,"
simtime = 50000
ntp = "ntp=1,"
ntb = "ntb=1,"
annealing = "ntr=1, restraintmask=':1-100 & !@H=', restraint_wt=10.0,"
residuenum = 100
weights = [1000.0, 500.0, 200.0]
number = 1
temperature = "temp0=0.0, tempi=0.0, temp0=300.0,"
print(
    heatinput(
        restart_input,
        simtime,
        ntp,
        ntb,
        annealing,
        residuenum,
        weights,
        number,
        temperature,
    )
)

print(pbsheader("foodin"))
