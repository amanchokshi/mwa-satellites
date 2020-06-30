"""
Chronological Ephemeris
-----------------------

Collate ephemeris data generated by :mod:`~embers.sat_utils.sat_ephemeris` for multiple satellites
and determine all ephemeris present in 30 minute observation windows. Save chronological ephemeris 
data to json files in :samp:`./embers_out/sat_utils/ephem_chrono`

"""

import sys
import argparse
from pathlib import Path
from embers.sat_utils.chrono_ephem import save_chrono_ephem

_parser = argparse.ArgumentParser(
    description="""
    Create chronological ephemeris json files
    """
)

_parser.add_argument(
    "--time_zone",
    metavar="\b",
    default="Australia/Perth",
    help="pytz timezone, default=Australia/Perth",
)
_parser.add_argument(
    "--start_date", metavar="\b", default="", help="start date in YYYY-MM-DD format"
)
_parser.add_argument(
    "--stop_date", metavar="\b", default="", help="stop date in YYYY-MM-DD format"
)
_parser.add_argument(
    "--interp_type",
    metavar="\b",
    default="cubic",
    help="Interpolation type. Default=cubic",
)
_parser.add_argument(
    "--interp_freq",
    metavar="\b",
    type=int,
    default=1,
    help="Interpolation frequency. Default=1",
)
_parser.add_argument(
    "--ephem_dir",
    metavar="\b",
    default="./embers_out/sat_utils/ephem_data",
    help="Directory where npz ephemeris files are saved. Default: ./embers_out/sat_utils/ephem_data",
)
_parser.add_argument(
    "--out_dir",
    metavar="\b",
    default="./embers_out/sat_utils/ephem_chrono",
    help="Dir where chrono_ephem json files will be saved. Default=./embers_out/sat_utils/ephem_chrono",
)

_args = _parser.parse_args()
_time_zone = _args.time_zone
_start_date = _args.start_date
_stop_date = _args.stop_date
_interp_type = _args.interp_type
_interp_freq = _args.interp_freq
_ephem_dir = _args.ephem_dir
_out_dir = _args.out_dir


if _start_date == "":
    print("-------------------------------------------")
    print("No input dates provided")
    print(">>> chrono_ephem --help, for more options")
    print("-------------------------------------------")


def main():
    """Execute chrono_ephem from terminal."""

    print(f"Saving chronological Ephem files to: {_out_dir}")
    print(f"Grab a coffee, this may take a couple of minutes!")

    # save log file
    Path(_out_dir).mkdir(parents=True, exist_ok=True)
    sys.stdout = open(f"{_out_dir}/chrono_ephem.log", "a")

    save_chrono_ephem(
        _time_zone,
        _start_date,
        _stop_date,
        _interp_type,
        _interp_freq,
        _ephem_dir,
        _out_dir,
    )