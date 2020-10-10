# Script to determine the differece in power between the FEE/measured maps along cardinal slices
# More power measured alone more sensitive axis of the dipole - perpendicular to dipole
# And vice-versa

# Rotation of reference tiles

import argparse
from pathlib import Path

import matplotlib
import numpy as np
from astropy.stats import mad_std as mad
from embers.rf_tools.colormaps import spectral
from embers.tile_maps.beam_utils import (chisq_fit_gain,
                                         healpix_cardinal_slices, map_slices,
                                         poly_fit, rotate_map)
from matplotlib import pyplot as plt

matplotlib.use("Agg")
_spec, _ = spectral()

parser = argparse.ArgumentParser(
    description="""
    Tile Slices paper plot
    """
)

parser.add_argument(
    "--out_dir",
    metavar="\b",
    default="../embers_out/paper_plots/tile_slices/",
    help="Output directory. Default=../embers_out/paper_plots",
)
parser.add_argument(
    "--map_dir",
    metavar="\b",
    default="../embers_out/tile_maps/tile_maps/tile_maps_clean/",
    help="Tile map directory. Default=../embers_out/tile_maps/tile_maps/tile_maps_clean",
)
parser.add_argument(
    "--fee_map",
    metavar="\b",
    default="../embers_out/mwa_utils/mwa_fee/mwa_fee_beam.npz",
    help="Healpix FEE map of mwa tile. default=../embers_out/mwa_utils/mwa_fee/mwa_fee_beam.npz",
)
parser.add_argument(
    "--nside", metavar="\b", type=int, default=32, help="Healpix Nside. Default = 32",
)

args = parser.parse_args()

out_dir = Path(args.out_dir)
map_dir = Path(args.map_dir)
fee_map = args.fee_map
nside = args.nside

# make output dir if it doesn't exist
out_dir.mkdir(parents=True, exist_ok=True)

tiles = [
    "S06",
    "S07",
    "S08",
    "S09",
    "S10",
    "S12",
    "S29",
    "S30",
    "S31",
    "S32",
    "S33",
    "S34",
    "S35",
    "S36",
]

refs = ["rf1"]

tile_pairs = []
for r in refs:
    for t in tiles:
        tile_pairs.append([t, r])


def beam_slices(map_file, fee_map, nside):
    """Returns pairs of [NS,EW] slices of maps, for each pointing"""

    t_name, r_name, _, _ = Path(map_file).stem.split("_")

    pointings = ["0", "2", "4"]

    maps = []

    # load data from map .npz file
    tile_map = np.load(map_file, allow_pickle=True)
    fee_m = np.load(fee_map, allow_pickle=True)

    for p in pointings:

        tile = tile_map[p]

        if "XX" in t_name:
            fee = fee_m[p][0]
        else:
            fee = fee_m[p][1]

        # rotate maps so slices can be taken
        fee_r = rotate_map(nside, angle=-np.pi / 4, healpix_array=fee)
        tile_r = rotate_map(nside, angle=-np.pi / 4, healpix_array=tile)

        #  fee_r[PB_0] = np.nan
        #  tile_r[PB_0] = np.nan

        # slice the tile and fee maps along NS, EW
        # zenith angle thresh of 70 to determine fit gain factor
        NS_f, EW_f = healpix_cardinal_slices(nside, fee_r, 70)
        NS_t, EW_t = map_slices(nside, tile_r, 70)

        gain_NS = chisq_fit_gain(data=NS_t[0], model=NS_f[0])
        gain_EW = chisq_fit_gain(data=EW_t[0], model=EW_f[0])

        # slice the tile and fee maps along NS, EW.
        # the above gain factor is applied to full beam slices
        NS_fee, EW_fee = healpix_cardinal_slices(nside, fee_r, 90)
        NS_tile, EW_tile = map_slices(nside, tile_r, 90)

        # Scale the data so that it best fits the beam slice
        NS_tile_med = NS_tile[0] - gain_NS[0]
        EW_tile_med = EW_tile[0] - gain_EW[0]

        # delta powers
        del_NS = NS_tile_med - NS_fee[0]
        del_EW = EW_tile_med - EW_fee[0]

        # 3rd order poly fits for residuals
        fit_NS = poly_fit(NS_tile[2], del_NS, NS_tile[0], 3)
        fit_EW = poly_fit(EW_tile[2], del_EW, EW_tile[0], 3)

        maps.append(
            [
                [NS_tile, NS_fee, NS_tile_med, del_NS, fit_NS],
                [EW_tile, EW_fee, EW_tile_med, del_EW, fit_EW],
            ]
        )

    return maps


def slice_residual():

    NS_r_XX = []
    NS_r_YY = []
    EW_r_XX = []
    EW_r_YY = []

    for tile in tiles:

        for pol in ["XX", "YY"]:

            f_tile = f"{map_dir}/{tile}{pol}_rf1{pol}_tile_maps.npz"

            try:
                map_slices = beam_slices(f_tile, fee_map, nside)

                #  pointings = ["0", "2", "4"]
                pointings = ["0"]

                for i, p in enumerate(pointings):
                    slices = map_slices[i]
                    NS_slices = slices[0]
                    fee_slice = NS_slices[1][0]
                    NS_med = NS_slices[0][0]
                    nulls = np.where(fee_slice < -30)
                    fee_slice[nulls] = np.nan
                    NS_med[nulls] = np.nan
                    NS_resi = np.array(NS_med - fee_slice)
                    if pol == "XX":
                        NS_r_XX.append(NS_resi)
                    else:
                        NS_r_YY.append(NS_resi)

                    EW_slices = slices[1]
                    fee_slice = EW_slices[1][0]
                    EW_med = EW_slices[0][0]
                    nulls = np.where(fee_slice < -30)
                    fee_slice[nulls] = np.nan
                    EW_med[nulls] = np.nan
                    EW_resi = np.array(EW_med - fee_slice)
                    if pol == "XX":
                        EW_r_XX.append(EW_resi)
                    else:
                        EW_r_YY.append(EW_resi)

            except Exception as e:
                print(e)

    NS_XX_res = np.nanmedian(np.array(NS_r_XX), axis=0)
    NS_YY_res = np.nanmedian(np.array(NS_r_YY), axis=0)
    EW_XX_res = np.nanmedian(np.array(EW_r_XX), axis=0)
    EW_YY_res = np.nanmedian(np.array(EW_r_YY), axis=0)

    NS_XX_mad = mad(np.array(NS_r_XX), axis=0)
    NS_YY_mad = mad(np.array(NS_r_YY), axis=0)
    EW_XX_mad = mad(np.array(EW_r_XX), axis=0)
    EW_YY_mad = mad(np.array(EW_r_YY), axis=0)

    # Only used to extract za arrays
    f_tile = f"{map_dir}/S06XX_rf0XX_tile_maps.npz"
    map_slices = beam_slices(f_tile, fee_map, nside)

    za = map_slices[0][0][0][2]

    NS_XX_fit = poly_fit(za, NS_XX_res, NS_XX_res, 2)
    NS_YY_fit = poly_fit(za, NS_YY_res, NS_YY_res, 2)
    EW_XX_fit = poly_fit(za, EW_XX_res, EW_XX_res, 2)
    EW_YY_fit = poly_fit(za, EW_YY_res, EW_YY_res, 2)

    # Plotting stuff
    plt.style.use("seaborn")

    nice_fonts = {
        "font.family": "sans-serif",
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "font.size": 8,
        "legend.fontsize": 6,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    }

    plt.rcParams.update(nice_fonts)

    plt.figure(figsize=(3.6, 2.4))

    #  colors = _spec(np.linspace(0.17, 0.9, 4))
    colors = _spec([0.14, 0.77, 0.66, 0.35])

    #  plt.figure(figsize=(6, 5))
    #  plt.errorbar(
    #  za,
    #  NS_XX_res,
    #  yerr=NS_XX_mad,
    #  fmt=".",
    #  ms=7,
    #  alpha=0.88,
    #  color=colors[0],
    #  elinewidth=1.4,
    #  capsize=1.4,
    #  capthick=1.6,
    #  )
    #  plt.errorbar(
    #  za,
    #  NS_YY_res,
    #  yerr=NS_YY_mad,
    #  fmt=".",
    #  ms=7,
    #  alpha=0.88,
    #  color=colors[1],
    #  elinewidth=1.4,
    #  capsize=1.4,
    #  capthick=1.6,
    #  )
    #  plt.errorbar(
    #  za,
    #  EW_XX_res,
    #  yerr=EW_XX_mad,
    #  fmt=".",
    #  ms=7,
    #  alpha=0.88,
    #  color=colors[2],
    #  elinewidth=1.4,
    #  capsize=1.4,
    #  capthick=1.6,
    #  )
    #  plt.errorbar(
    #  za,
    #  EW_YY_res,
    #  yerr=EW_YY_mad,
    #  fmt=".",
    #  ms=7,
    #  alpha=0.88,
    #  color=colors[3],
    #  elinewidth=1.4,
    #  capsize=1.4,
    #  capthick=1.6,
    #  )

    plt.scatter(
        za,
        NS_XX_res,
        s=16,
        alpha=0.88,
        edgecolor="black",
        linewidth=0.2,
        color=colors[0],
    )
    plt.scatter(
        za,
        NS_YY_res,
        s=16,
        alpha=0.88,
        edgecolor="black",
        linewidth=0.2,
        color=colors[1],
    )
    plt.scatter(
        za,
        EW_XX_res,
        s=16,
        alpha=0.88,
        edgecolor="black",
        linewidth=0.2,
        color=colors[2],
    )
    plt.scatter(
        za,
        EW_YY_res,
        s=16,
        alpha=0.88,
        edgecolor="black",
        linewidth=0.2,
        color=colors[3],
    )

    plt.plot(za, NS_XX_fit, label="NS_XX", linewidth=2, color=colors[0])
    plt.plot(za, NS_YY_fit, label="NS_YY", linewidth=2, color=colors[1])
    plt.plot(za, EW_XX_fit, label="EW_XX", linewidth=2, color=colors[2])
    plt.plot(za, EW_YY_fit, label="EW_YY", linewidth=2, color=colors[3])

    leg = plt.legend(loc="upper right", frameon=True, markerscale=4, handlelength=1)
    leg.get_frame().set_facecolor("white")
    for le in leg.legendHandles:
        le.set_alpha(1)

    plt.ylim([-4, 4])
    plt.xlabel("Zenith Angle [degrees]")
    plt.ylabel("Residual Power [dB]")
    plt.tight_layout()
    plt.savefig("ref_rot/rot_resi.pdf")


slice_residual()
