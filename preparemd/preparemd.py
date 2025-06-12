from argparse import ArgumentParser

from preparemd.amber.md import prepareinputs, writetrajfix
from preparemd.amber.top import makeleapin
from preparemd.utils.log import log_setup

log_setup(level="INFO")


def main():
    parser = ArgumentParser(
        description="Prepare MD input files using the provided PDB file and options."
    )
    parser.add_argument("--file", "-f", required=True, help="Path to input pdb file.")
    parser.add_argument(
        "--distdir",
        "-o",
        required=True,
        help="Path to a directory that will store top and amber files.",
    )
    parser.add_argument(
        "--strip",
        default="",
        help=(
            "If provided, the specified region will be removed from MD simulations. "
            "This is useful for signal peptides, for example."
        ),
    )
    parser.add_argument(
        "--num_mddir",
        type=int,
        default=3,
        help="Number of directories that will be made in the amber/pr directory. Default is 3.",
    )
    parser.add_argument(
        "--ns_per_mddir",
        type=int,
        default=50,
        help=(
            "Nanoseconds of MD simulations in each production run directory "
            "(amber/pr/001, 002, ...). Default is 50 (ns)."
        ),
    )
    parser.add_argument(
        "--ion_conc",
        type=int,
        default=150,
        help=(
            "Ion concentration in the periodic boundary box of MD simulations. "
            "Default is 150 (mM)."
        ),
    )
    parser.add_argument(
        "--boxsize",
        default="",
        help=(
            "The periodic boundary box for MD simulations will be this value, if provided. "
            'For example, "120 120 120" will be a cube box with 120 Å on a side. '
            "If no value is specified, the box size is automatically assigned "
            "with 10 Å margins in the x, y, and z directions."
        ),
    )
    parser.add_argument(
        "--rotate",
        default="",
        help=(
            'Rotate the solute. For example, "x 90" will rotate the solute 90 degrees around the x-axis.'
        ),
    )
    parser.add_argument(
        "--trajprefix",
        "-t",
        default="",
        help=(
            'Prefix of trajectory. This is used in the "trajfix.in" file. e.g. "S36S36".'
        ),
    )
    parser.add_argument(
        "--sslink",
        default="",
        help=(
            'Input sslink file. e.g. "pre_sslink". '
            "This file format is the same as an output sslink file of pdb4amber. "
            "Set this value if you have a correct pair SS-bond list."
        ),
    )
    parser.add_argument(
        "--machineenv",
        "-m",
        choices=["foodin", "flow", "yayoi", "tsubame"],
        default="foodin",
        help=(
            "Choose server clusters where you want to run. "
            "This will change the qsub/pjsub header lines. Default: foodin."
        ),
    )
    parser.add_argument(
        "--frcmod",
        nargs="*",
        default=None,
        help="Path to additional frcmod files. Multiple files can be specified.",
    )
    parser.add_argument(
        "--prep",
        nargs="*",
        default=None,
        help="Path to additional AMBER prep files. Multiple files can be specified.",
    )
    parser.add_argument(
        "--mol2",
        action="append",
        default=None,
        help="Path to additional mol2 files. The flag can be specified more than once on the command line.",
    )
    parser.add_argument(
        "--fftype",
        choices=["ff14SB", "ff19SB"],
        default="ff19SB",
        help="Choose AMBER force field type. Default: ff19SB",
    )
    parser.add_argument(
        "--run_leap",
        action="store_true",
        default=True,
        help=(
            "Whether to run the leap process. "
            "Turning leap process off may be useful to prepare only amber MD files."
        ),
    )
    args = parser.parse_args()

    if args.num_mddir < 1:
        raise ValueError("The num_mddir argument must be 1 or more.")
    if args.ns_per_mddir < 1:
        raise ValueError("The ns_per_mddir argument must be 1 or more.")
    if args.ion_conc < 1:
        raise ValueError("The ion_conc argument must be 1 or more.")

    resnumber, sslink_file = prepareinputs.run_pdb4amber(
        args.file, args.distdir, strip=args.strip, sslink_file=args.sslink
    )
    pre2boxsize = prepareinputs.preparepre2file(
        args.distdir, rotate=args.rotate, sslink_file=sslink_file
    )
    prepareinputs.cys_to_cyx_in_pre2file(args.distdir, sslink_file=sslink_file)
    makeleapin.makeleapin(
        args.distdir,
        boxsize=args.boxsize,
        pre2boxsize=pre2boxsize,
        ion_conc=args.ion_conc,
        sslink_file=sslink_file,
        fftype=args.fftype,
        frcmod=args.frcmod,
        prep=args.prep,
        mol2=args.mol2,
    )
    if args.run_leap:
        prepareinputs.run_leap(args.distdir, args.boxsize, pre2boxsize)
    prepareinputs.prepareamberfiles(
        args.distdir, resnumber, args.num_mddir, args.ns_per_mddir, args.machineenv
    )
    writetrajfix.writetrajfix(args.distdir, resnumber, args.num_mddir, args.trajprefix)


if __name__ == "__main__":
    main()
