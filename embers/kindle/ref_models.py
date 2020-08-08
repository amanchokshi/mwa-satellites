"""
Reference FEKO Models
---------------------

Create and save a reference healpix model and plot to ``./embers_out/tile_maps/ref_models``

"""

import argparse

from embers.tile_maps.ref_fee_healpix import ref_healpix_save

_parser = argparse.ArgumentParser(
    description="""
    Create and save reference healpix models
    """
)

_parser.add_argument(
    "--nside", metavar="\b", type=int, default=32, help="Healpix nide. Default: 32"
)
_parser.add_argument(
    "--out_dir",
    metavar="\b",
    default="embers_out/tile_maps/ref_models",
    help="Dir where reference models are saved. Default=./embers_out/tile_maps/ref_models",
)

_args = _parser.parse_args()
_nside = _args.nside
_out_dir = _args.out_dir

def main():
    """Execute ref_healpix_save reference models from terminal"""

    print(f"Reference models saved to {_out_dir}")
    ref_healpix_save(_nside, _out_dir)