"""
Tile Maps
----------

A set of tools to project satellite passes onto a healpix map according to their ephemeris.

"""

import argparse
import concurrent.futures
import json
import sys
from itertools import repeat
from pathlib import Path

import healpy as hp
import matplotlib
import numpy as np
from embers.rf_tools.colormaps import spectral
from embers.rf_tools.rf_data import tile_names
from embers.sat_utils.sat_channels import (noise_floor, read_aligned,
                                           time_filter, time_tree)
from embers.sat_utils.sat_list import norad_ids
from embers.tile_maps.beam_utils import rotate_map
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy import optimize as opt
from scipy.stats import binned_statistic, chisquare

matplotlib.use("Agg")
cmap, _ = spectral()


def check_pointing(timestamp, obs_point_json):
    """Check if timestamp is at MWA sweet-pointing 0, 2, 4, 41.

    :param timestamp: time at which MWA pointing is to be checked
    :param obs_point_json: Path to :samp:`obs_point.json` output from :func:`~embers.mwa_utils.mwa_pointings.obs_pointings`

    :returns:
        - Pointing of MWA at given :samp:`timestamp`

    """

    # Read observation pointing list
    with open(obs_point_json) as point:
        obs_p = json.load(point)
        point_0 = obs_p["point_0"]
        point_2 = obs_p["point_2"]
        point_4 = obs_p["point_4"]
        point_41 = obs_p["point_41"]

    if timestamp in point_0:
        point = 0
    elif timestamp in point_2:
        point = 2
    elif timestamp in point_4:
        point = 4
    elif timestamp in point_41:
        point = 41
    else:
        point = None

    return point


def chisq_fit_gain(data=None, model=None):
    """Chisqaured fit the data and model.

    :param data: A data array to be fit to a model. Typically this if rf map data being fit to the fee model
    :param model: The model to which the data is being fit. Typically the fee beam model

    :returns:
        - Single multiplicative gain value, which best fits data to model

    """

    bad_values = np.isnan(data)
    data = data[~bad_values]
    model = model[~bad_values]

    def chisqfunc(gain):
        mod = model + gain
        chisq = sum((data - mod) ** 2)
        return chisq

    x0 = np.array([0])

    result = opt.minimize(chisqfunc, x0)

    return result.x


def test_chisq_fit(data=None, model=None, offset=20):
    """chi-squared test for goodness of fit betweet model and data

    :param data: A data array to be fit to a model. Typically this if rf map data being fit to the fee model
    :param model: The model to which the data is being fit. Typically the fee beam model
    :param offset: An integer offset by which data and model can be shifted away from their original 0 peak, which pvalues struggle with. Default=20

    :returns:
        - pvalue - an indicator for goodess of fit
    """

    bad_values = np.isnan(data)
    data = data[~bad_values]
    model = model[~bad_values]

    data = np.asarray(data) - np.nanmin(model) + offset
    model = np.asarray(model) - np.nanmin(model) + offset

    _, pvalue = chisquare(data, f_exp=model)

    return pvalue


def plt_channel(
    out_dir,
    times,
    ref,
    tile,
    ref_noise,
    tile_noise,
    chan_num,
    sat_id,
    pointing,
    timestamp,
):

    """Plot power in a frequency channel of raw rf data, with various thresholds

    :param out_dir: Output directory where plot will be saved
    :param times: Time array
    :param ref: Reference antenna rf power array
    :param tile: MWA tile rf power array
    :param ref_noise: Reference noise threshold
    :param tile_noise: MWA tile noise threshold
    :param chan_num: Channel Number
    :param sat_id: Norad Cat ID
    :param pointing: MWA sweet pointing of the observation
    :param timestamp: Observation timestamp

    :returns:
        - A plot of channel power with multiple power thresholds is saved to :samp:`out_dir`

    """

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn")

    fig = plt.figure(figsize=(8, 6))
    fig.suptitle(
        f"Satellite [{sat_id}] Pass @ {timestamp} in Channel: [{chan_num}]", y=0.98
    )

    ax1 = fig.add_subplot(2, 1, 1)
    ax1.plot(
        times, ref, linestyle="-", linewidth=2, alpha=1.0, color="#729d39", label="ref",
    )
    ax1.fill_between(times, y1=ref, y2=-120, color="#729d39", alpha=0.7)
    ax1.axhline(
        ref_noise,
        linestyle="-",
        linewidth=2,
        color="#36622b",
        label=f"Ref Cut: {ref_noise:.2f} dBm",
    )
    ax1.axhspan(-120, ref_noise, color="#36622b", alpha=0.7)
    ax1.set_ylim([min(ref) - 1, max(ref) + 1])
    ax1.set_ylabel("Power [dBm]")
    ax1.set_xticklabels([])

    leg = ax1.legend(frameon=True)
    leg.get_frame().set_facecolor("grey")
    leg.get_frame().set_alpha(0.2)
    for le in leg.legendHandles:
        le.set_alpha(1)

    ax2 = fig.add_subplot(2, 1, 2)
    ax2.plot(
        times,
        tile,
        linestyle="-",
        linewidth=2,
        alpha=1.0,
        color="#ff5656",
        label="tile",
    )
    ax2.fill_between(times, y1=tile, y2=-120, color="#ff5656", alpha=0.7)
    ax2.axhline(
        tile_noise,
        linestyle="-",
        linewidth=2,
        color="#970747",
        label=f"Tile Cut: {tile_noise:.2f} dBm",
    )
    ax2.axhspan(-120, tile_noise, color="#970747", alpha=0.7)
    ax2.set_ylim([min(tile) - 1, max(tile) + 1])
    ax2.set_ylabel("Power [dBm]")
    ax2.set_xlabel("Time [s]")

    leg = ax2.legend(frameon=True)
    leg.get_frame().set_facecolor("grey")
    leg.get_frame().set_alpha(0.2)
    for le in leg.legendHandles:
        le.set_alpha(1)

    plt.tight_layout()
    plt.subplots_adjust(top=0.94)
    plt.savefig(f"{out_dir}/{timestamp}_{sat_id}_{chan_num}_channel.png")
    plt.close()


def plt_fee_fit(
    times, mwa_fee_pass, mwa_pass_fit_raw, mwa_pass_fit, out_dir, point, timestamp, sat
):
    """Plot data and model with goodness of fit p-value to visualize the degree of fit

    :param times: Time array
    :param mwa_fee_pass: MWA fee model slices according to satellite pass ephemeris
    :param mwa_pass_fit_raw: Satellite rf data from MWA tiles
    :param mwa_pass_fit: Satellite rf data from MWA tiles, fit to the fee model
    :param out_dir: Output directory where plot will be saved
    :param point: MWA sweet pointing of the observation
    :param timestamp:  Observation timestamp
    :param sat_id: Norad Cat ID

    :returns:
        - Plot comparing MWA fee model slice to satellite data, before and after gain power corrections

    """

    pval = test_chisq_fit(data=mwa_pass_fit, model=mwa_fee_pass)

    plt.style.use("seaborn")

    fig = plt.figure(figsize=(8, 6))
    ax1 = fig.add_subplot(1, 1, 1)

    ax1.scatter(
        times, mwa_fee_pass, color="#c70039", alpha=0.6, marker=".", label="FEE model"
    )

    ax1.scatter(
        times,
        mwa_pass_fit_raw,
        color="#7da87b",
        alpha=0.9,
        marker=".",
        label="RF data raw",
    )
    ax1.set_ylim(-50, 2)

    ax1.scatter(
        times,
        mwa_pass_fit,
        color="#4f8a8b",
        alpha=0.9,
        marker=".",
        label="RF gain calibrated",
    )
    ax1.set_ylim(-50, 2)
    ax1.set_ylabel("Power [dBm]")
    ax1.set_xticklabels([])

    leg = ax1.legend(frameon=True)
    leg.get_frame().set_facecolor("grey")
    leg.get_frame().set_alpha(0.2)
    for le in leg.legendHandles:
        le.set_alpha(1)

    delta_p_raw = np.array(mwa_fee_pass) - np.array(mwa_pass_fit_raw)
    delta_p = np.array(mwa_fee_pass) - np.array(mwa_pass_fit)

    divider = make_axes_locatable(ax1)
    dax = divider.append_axes("bottom", size="40%", pad=0.10)

    dax.scatter(
        times,
        delta_p_raw,
        color="#7da87b",
        alpha=0.9,
        marker=".",
        s=36,
        label="Raw residuals",
    )

    dax.scatter(
        times,
        delta_p,
        color="#4f8a8b",
        alpha=0.9,
        marker=".",
        s=36,
        label="Calibrated residuals",
    )

    leg = dax.legend(loc="lower left", frameon=True, markerscale=2, handlelength=1)
    leg.get_frame().set_facecolor("grey")
    leg.get_frame().set_alpha(0.4)
    for le in leg.legendHandles:
        le.set_alpha(1)
    dax.set_xlabel("Times [min]")
    dax.set_yticks([-20, 0, 20])
    dax.set_ylabel(r"$\Delta$P [dBm]")

    plt.title(f"Goodness of Fit: {pval} ")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/{point}/{timestamp}_{sat}.png")
    plt.close()


def rf_apply_thresholds(
    ali_file,
    chrono_file,
    sat_id,
    sat_chan,
    sat_thresh,
    noi_thresh,
    pow_thresh,
    point,
    plots,
    out_dir,
):

    """Apply power, noise thresholds to rf data arrays.

    For a particular NORAD sat ID, crop a pair of ref, tile data arrays to when the satellite is above the horizon
    as indicated by it's ephemeris. Given the frequency channel in which the satellite transmits, extract the channel
    power and return a coherent data set with ephemeris and tile power in a tuple

    :param ali_file: :class:`~pathlib.PurePosixPath` to a aligned ref, tile data file, output from :func:`~embers.rf_tools.align_data.save_aligned`
    :param chrono_file: :class:`~pathlib.PurePosixPath` to chrono ephemeris file, output from :func:`~embers.sat_utils.chrono_ephem.save_chrono_ephem`
    :param sat_id: Norad catalogue ID
    :param sat_chan: Transmission channel of given :samp:`sat_id`
    :param sat_thresh: σ threshold to detect sats in the computation of rf data noise_floor. A good default is 1
    :param noi_thresh: Noise Threshold: Multiples of MAD. 3 is a good default
    :param pow_thresh: Peak power which must be exceeded for satellite pass to be considered
    :param point: MWA sweet pointing of the observation
    :param plots: if :samp:`True` create diagnostic plots
    :param out_dir: Output directory where plot will be saved

    :returns:
        - :class:`~tuple` of (ref_power, tile_power, alt, az, times) where all thresholds were met. If no data passes all thresholds 0 returned

    """

    ref, tile, timestamp, _ = ali_file.stem.split("_")

    ref_p, tile_p, times = read_aligned(ali_file=ali_file)

    ref_noise = noise_floor(sat_thresh, noi_thresh, ref_p)
    tile_noise = noise_floor(sat_thresh, noi_thresh, tile_p)

    with open(chrono_file) as chrono:
        chrono_ephem = json.load(chrono)

        norad_list = [chrono_ephem[s]["sat_id"][0] for s in range(len(chrono_ephem))]

        norad_index = norad_list.index(str(sat_id))

        norad_ephem = chrono_ephem[norad_index]

        rise_ephem = norad_ephem["time_array"][0]
        set_ephem = norad_ephem["time_array"][-1]

        intvl = time_filter(rise_ephem, set_ephem, np.asarray(times))

        if intvl is not None:

            w_start, w_stop = intvl

            # Slice [crop] the ref/tile/times arrays to the times of sat pass and extract sat_chan
            ref_c = ref_p[w_start : w_stop + 1, sat_chan]
            tile_c = tile_p[w_start : w_stop + 1, sat_chan]
            times_c = times[w_start : w_stop + 1]

            alt = np.asarray(norad_ephem["sat_alt"])
            az = np.asarray(norad_ephem["sat_az"])

            if (np.nanmax(ref_c - ref_noise) >= pow_thresh) and (
                np.nanmax(tile_c - tile_noise) >= pow_thresh
            ):

                # Apply noise criteria. In the window, where are ref_power and tile power
                # above their respective thresholds?
                if np.where((ref_c >= ref_noise) & (tile_c >= tile_noise))[0].size != 0:
                    good_ref = ref_c[
                        np.where((ref_c >= ref_noise) & (tile_c >= tile_noise))[0]
                    ]
                    good_tile = tile_c[
                        np.where((ref_c >= ref_noise) & (tile_c >= tile_noise))[0]
                    ]
                    good_alt = alt[
                        np.where((ref_c >= ref_noise) & (tile_c >= tile_noise))[0]
                    ]
                    good_az = az[
                        np.where((ref_c >= ref_noise) & (tile_c >= tile_noise))[0]
                    ]

                    if plots is True:
                        plt_channel(
                            f"{out_dir}/pass_plots/{tile}_{ref}/{point}",
                            times_c,
                            ref_c,
                            tile_c,
                            ref_noise,
                            tile_noise,
                            sat_chan,
                            sat_id,
                            point,
                            timestamp,
                        )

                    return [good_ref, good_tile, good_alt, good_az, times_c]

                else:
                    return 0

            else:
                return 0

        else:
            return 0


def rfe_calibration(
    start_date,
    stop_date,
    tile_pair,
    sat_thresh,
    noi_thresh,
    pow_thresh,
    ref_model,
    fee_map,
    nside,
    obs_point_json,
    align_dir,
    chrono_dir,
    chan_map_dir,
    out_dir,
):

    resi_gain = {}
    resi_gain["pass_data"] = []
    resi_gain["pass_resi"] = []

    ref, tile = tile_pair

    dates, timestamps = time_tree(start_date, stop_date)

    # Load reference FEE model
    # Rotate the fee models by -pi/2 to move model from spherical (E=0) to Alt/Az (N=0)
    ref_fee_model = np.load(ref_model, allow_pickle=True)

    fee_m = np.load(fee_map, allow_pickle=True)

    if "XX" in tile:
        ref_fee = ref_fee_model["XX"]
        rotated_fee = rotate_map(nside, angle=-(1 * np.pi) / 2.0, healpix_array=ref_fee)
    else:
        ref_fee = ref_fee_model["YY"]
        rotated_fee = rotate_map(nside, angle=-(1 * np.pi) / 2.0, healpix_array=ref_fee)

    for day in range(len(dates)):

        for window in range(len(timestamps[day])):
            timestamp = timestamps[day][window]

            # pointing at timestamp
            point = check_pointing(timestamp, obs_point_json)

            if point == 0:

                if "XX" in tile:
                    mwa_fee = fee_m[str(point)][0]
                else:
                    mwa_fee = fee_m[str(point)][1]

                ali_file = Path(
                    f"{align_dir}/{dates[day]}/{timestamp}/{ref}_{tile}_{timestamp}_aligned.npz"
                )

                # check if file exists
                if ali_file.is_file():

                    # Chrono and map Ephemeris file
                    chrono_file = Path(f"{chrono_dir}/{timestamp}.json")
                    channel_map = Path(f"{chan_map_dir}/{timestamp}.json")

                    with open(chrono_file) as chrono:
                        chrono_ephem = json.load(chrono)

                        if chrono_ephem != []:

                            norad_list = [
                                chrono_ephem[s]["sat_id"][0]
                                for s in range(len(chrono_ephem))
                            ]

                            if norad_list != []:

                                if channel_map.is_file():

                                    with open(channel_map) as ch_map:
                                        chan_map = json.load(ch_map)

                                        chan_sat_ids = [
                                            int(i) for i in list(chan_map.keys())
                                        ]

                                        for sat in chan_sat_ids:

                                            chan = chan_map[f"{sat}"]

                                            sat_data = rf_apply_thresholds(
                                                ali_file,
                                                chrono_file,
                                                sat,
                                                chan,
                                                sat_thresh,
                                                noi_thresh,
                                                pow_thresh,
                                                point,
                                                False,
                                                out_dir,
                                            )

                                            if sat_data != 0:

                                                (
                                                    ref_power,
                                                    tile_power,
                                                    alt,
                                                    az,
                                                    times,
                                                ) = sat_data

                                                # Altitude is in deg while az is in radians
                                                # convert alt to radians
                                                # za - zenith angle
                                                alt = np.radians(alt)
                                                za = np.pi / 2 - alt
                                                az = np.asarray(az)

                                                # Now convert to healpix coordinates
                                                # healpix_index = hp.ang2pix(nside,θ, ɸ)
                                                healpix_index = hp.ang2pix(
                                                    nside, za, az
                                                )

                                                # multiple data points fall within a single healpix pixel
                                                # find the unique pixels
                                                u = np.unique(healpix_index)

                                                ref_pass = np.array(
                                                    [
                                                        np.nanmean(
                                                            ref_power[
                                                                np.where(
                                                                    healpix_index == i
                                                                )[0]
                                                            ]
                                                        )
                                                        for i in u
                                                    ]
                                                )

                                                tile_pass = np.array(
                                                    [
                                                        np.nanmean(
                                                            tile_power[
                                                                np.where(
                                                                    healpix_index == i
                                                                )[0]
                                                            ]
                                                        )
                                                        for i in u
                                                    ]
                                                )

                                                times_pass = np.array(
                                                    [
                                                        np.mean(
                                                            times[
                                                                np.where(
                                                                    healpix_index == i
                                                                )
                                                            ][0]
                                                        )
                                                        for i in u
                                                    ]
                                                )

                                                ref_fee_pass = np.array(
                                                    [rotated_fee[i] for i in u]
                                                )

                                                mwa_fee_pass = np.array(
                                                    [mwa_fee[i] for i in u]
                                                )

                                                # This is the magic. Equation [1] of the paper
                                                # A measured cross sectional slice of the MWA beam
                                                mwa_pass = (
                                                    np.array(tile_pass)
                                                    - np.array(ref_pass)
                                                    + np.array(ref_fee_pass)
                                                )

                                                # RFE distortion is seen in tile_pass when raw power is above -30dBm
                                                # fit the mwa_pass data to the tile_pass power level
                                                # Mask everything below -30dBm to fit distorted MWA and tile pass
                                                peak_filter = np.where(tile_pass >= -30)
                                                offset = chisq_fit_gain(
                                                    data=tile_pass[peak_filter],
                                                    model=mwa_pass[peak_filter],
                                                )
                                                # This is a slice of the MWA beam, scaled back to the power level of the raw, distorted tile data
                                                mwa_pass = mwa_pass + offset[0]

                                                # Single multiplicative gain factor to fit MWA FEE beam slice down to tile pass power level
                                                # MWA pass Data above -50dBm masked out because it is distorted
                                                # Data below -60dBm maked out because FEE nulls are much deeper than the dynamic range of satellite passes
                                                dis_filter = np.where(mwa_pass <= -35)
                                                mwa_pass_fil = mwa_pass[dis_filter]
                                                mwa_fee_pass_fil = mwa_fee_pass[
                                                    dis_filter
                                                ]
                                                null_filter = np.where(
                                                    mwa_fee_pass_fil >= -55
                                                )

                                                offset = chisq_fit_gain(
                                                    data=mwa_pass_fil[null_filter],
                                                    model=mwa_fee_pass_fil[null_filter],
                                                )
                                                mwa_fee_pass = mwa_fee_pass + offset
                                                mwa_pass_fit = mwa_pass

                                                # more than 30 non distorted samples
                                                if (
                                                    mwa_fee_pass[dis_filter][
                                                        null_filter
                                                    ].size
                                                    >= 30
                                                ):

                                                    # determine how well the data fits the model with chi-square
                                                    pval = test_chisq_fit(
                                                        data=mwa_pass_fit[dis_filter][
                                                            null_filter
                                                        ],
                                                        model=mwa_fee_pass[dis_filter][
                                                            null_filter
                                                        ],
                                                    )

                                                    # a goodness of fit threshold
                                                    if pval >= 0.8:

                                                        # consider residuals of sats which pass within 10 deg of zenith
                                                        # an hp index of 111 approx corresponds to a zenith angle of 10 degrees
                                                        hp_10_deg = 111

                                                        if np.amin(u) <= hp_10_deg:

                                                            # only passes longer than 10 minutes
                                                            if (
                                                                np.amax(times_pass)
                                                                - np.amin(times_pass)
                                                            ) >= 600:

                                                                # residuals between scaled FEE and mwa pass
                                                                resi = (
                                                                    mwa_fee_pass
                                                                    - mwa_pass_fit
                                                                )
                                                                resi_gain[
                                                                    "pass_data"
                                                                ].extend(mwa_pass_fit)
                                                                resi_gain[
                                                                    "pass_resi"
                                                                ].extend(resi)

    # Save gain residuals to json file
    with open(f"{out_dir}/{tile}_{ref}_gain_fit.json", "w") as outfile:
        json.dump(resi_gain, outfile, indent=4)


def rfe_collate_cali(start_gain, stop_gain, rfe_cali_dir):

    # find all rfe_gain json files
    gain_files = [item for item in Path(rfe_cali_dir).glob("*.json")]

    # Combine data from all RF Explorers
    pass_data = []
    pass_resi = []

    for n, f in enumerate(gain_files):
        with open(f, "r") as data:
            rfe = json.load(data)
            pass_data.extend(rfe["pass_data"])
            pass_resi.extend(rfe["pass_resi"])

    plt.figure()

    plt.hexbin(pass_data, pass_resi, gridsize=121, cmap=cmap, alpha=0.99, zorder=0)

    pass_data = np.array(pass_data)
    pass_resi = np.array(pass_resi)

    # Clean up huge noisy outliers
    filtr = np.where(np.logical_and(pass_data <= -25, pass_data >= -65))
    pass_data = pass_data[filtr]
    pass_resi = pass_resi[filtr]

    # Median of binned data
    bin_med, bin_edges, binnumber = binned_statistic(
        pass_data, pass_resi, statistic="median", bins=16
    )
    bin_width = bin_edges[1] - bin_edges[0]
    bin_centers = bin_edges[1:] - bin_width / 2

    # Now look at data between -50, -30, where gains vary
    filtr = np.where(np.logical_and(pass_data >= start_gain, pass_data <= stop_gain))
    pass_data = pass_data[filtr]
    pass_resi = pass_resi[filtr]

    # Linear fit to RFE data between -50, -30 dBm
    poly = np.polyfit(pass_data, pass_resi, 2)

    # Mathematical function of fit, which can be evaluated anywhere
    f = np.poly1d(poly)

    # save polyfit to file
    np.save(f"{rfe_cali_dir}/rfe_gain_fit.npy", poly)

    # x_f = [f.roots[0], -45, -40, -35, -30, -25, -20]
    x_f = np.linspace(max(f.roots), -25, num=10)
    y_f = f(x_f)

    plt.plot(
        x_f,
        y_f,
        color="w",
        lw=2.1,
        marker="s",
        markeredgecolor="k",
        markeredgewidth=1.6,
        markersize=4.9,
        alpha=1,
        label="Gain fit",
        zorder=1,
    )
    plt.scatter(
        bin_centers,
        bin_med,
        marker="X",
        s=36,
        facecolors="#ee4540",
        lw=0.9,
        edgecolors="w",
        alpha=1,
        label="Median residuals",
        zorder=2,
    )

    leg = plt.legend(loc="lower right", frameon=True, markerscale=0.9, handlelength=1.4)
    leg.get_frame().set_facecolor("#cccccc")
    for le in leg.legendHandles:
        le.set_alpha(0.77)

    plt.xlabel("Observed power [dBm]")
    plt.ylabel("Residuals power [dB]")
    plt.xlim([-65, -25])
    plt.ylim([-10, 15])
    plt.tick_params(axis="both", length=0)
    plt.grid(color="#cccccc", alpha=0.36, lw=1.2)
    plt.box(None)
    plt.tight_layout()
    plt.savefig(f"{rfe_cali_dir}/rfe_gain_fit.png", bbox_inches="tight")


def rfe_batch_cali(
    start_date,
    stop_date,
    sat_thresh,
    noi_thresh,
    pow_thresh,
    ref_model,
    fee_map,
    nside,
    obs_point_json,
    align_dir,
    chrono_dir,
    chan_map_dir,
    out_dir,
):
    # Tile names
    refs = tile_names()[:4]
    tiles = tile_names()[4:]

    # All relevant tile pairs
    tile_pairs = []
    for ref in refs:
        if "XX" in ref:
            for tile in [t for t in tiles if "XX" in t]:
                tile_pairs.append([ref, tile])
        else:
            for tile in [t for t in tiles if "YY" in t]:
                tile_pairs.append([ref, tile])

    # Save logs
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Parallization magic happens here
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(
            rfe_calibration,
            repeat(start_date),
            repeat(stop_date),
            tile_pairs,
            repeat(sat_thresh),
            repeat(noi_thresh),
            repeat(pow_thresh),
            repeat(ref_model),
            repeat(fee_map),
            repeat(nside),
            repeat(obs_point_json),
            repeat(align_dir),
            repeat(chrono_dir),
            repeat(chan_map_dir),
            repeat(out_dir),
        )

    rfe_collate_cali(-50, -30, out_dir)


def project_tile_healpix(tile_pair, start_date, stop_date):

    ref, tile = tile_pair

    pointings = ["0", "2", "4", "41"]

    dates, timestamps = time_tree(start_date, stop_date)

    if plots == "True":
        Path(f"{out_dir}/pass_plots/{tile}_{ref}/0").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/pass_plots/{tile}_{ref}/2").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/pass_plots/{tile}_{ref}/4").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/pass_plots/{tile}_{ref}/41").mkdir(parents=True, exist_ok=True)

        Path(f"{out_dir}/fit_plots/{tile}_{ref}/0").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/fit_plots/{tile}_{ref}/2").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/fit_plots/{tile}_{ref}/4").mkdir(parents=True, exist_ok=True)
        Path(f"{out_dir}/fit_plots/{tile}_{ref}/41").mkdir(parents=True, exist_ok=True)

    # Initialize an empty dictionary for tile data
    # The map is list of length 12288 of empty lists to append pixel values to
    # keep track of which satellites contributed which data
    tile_data = {
        "mwa_maps": {
            p: [[] for pixel in range(hp.nside2npix(nside))] for p in pointings
        },
        "ref_maps": {
            p: [[] for pixel in range(hp.nside2npix(nside))] for p in pointings
        },
        "tile_maps": {
            p: [[] for pixel in range(hp.nside2npix(nside))] for p in pointings
        },
        "sat_map": {
            p: [[] for pixel in range(hp.nside2npix(nside))] for p in pointings
        },
        "times": {p: [[] for pixel in range(hp.nside2npix(nside))] for p in pointings},
    }

    # Load reference FEE model
    # Rotate the fee models by -pi/2 to move model from spherical (E=0) to Alt/Az (N=0)
    ref_fee_model = np.load(ref_model, allow_pickle=True)

    #    # Tile S33YY has it's 9th dipole flagged
    #    if tile is 'S33YY':
    #        fee_m = np.load(fee_map_flagged, allow_pickle=True)
    #    else:
    #        fee_m = np.load(fee_map, allow_pickle=True)
    fee_m = np.load(fee_map, allow_pickle=True)

    if "XX" in tile:
        ref_fee = ref_fee_model["XX"]
        rotated_fee = rotate_map(nside, angle=-(1 * np.pi) / 2.0, healpix_array=ref_fee)
    else:
        ref_fee = ref_fee_model["YY"]
        rotated_fee = rotate_map(nside, angle=-(1 * np.pi) / 2.0, healpix_array=ref_fee)

    for day in range(len(dates)):

        for window in range(len(date_time[day])):
            timestamp = date_time[day][window]

            # Check if at timestamp, reciever was pointed to 0,2,4,41 gridpointing
            if (
                (timestamp in point_0)
                or (timestamp in point_2)
                or (timestamp in point_4)
                or (timestamp in point_41)
            ):

                # pointing at timestamp
                point = check_pointing(timestamp, point_0, point_2, point_4, point_41)

                if "XX" in tile:
                    mwa_fee = fee_m[str(point)][0]
                else:
                    mwa_fee = fee_m[str(point)][1]

                ali_file = Path(
                    f"{align_dir}/{dates[day]}/{timestamp}/{ref}_{tile}_{timestamp}_aligned.npz"
                )

                # check if file exists
                if ali_file.is_file():

                    # Chrono and map Ephemeris file
                    chrono_file = Path(f"{chrono_dir}/{timestamp}.json")
                    channel_map = f"{map_dir}/{timestamp}.json"

                    with open(chrono_file) as chrono:
                        chrono_ephem = json.load(chrono)

                        if chrono_ephem != []:

                            norad_list = [
                                chrono_ephem[s]["sat_id"][0]
                                for s in range(len(chrono_ephem))
                            ]

                            if norad_list != []:

                                with open(channel_map) as ch_map:
                                    chan_map = json.load(ch_map)

                                    chan_sat_ids = [
                                        int(i) for i in list(chan_map.keys())
                                    ]

                                    for sat in chan_sat_ids:

                                        chan = chan_map[f"{sat}"]

                                        sat_data = rf_apply_thresholds(
                                            ali_file,
                                            chrono_file,
                                            sat,
                                            chan,
                                            pow_thresh,
                                            point,
                                            plots,
                                        )

                                        if sat_data != 0:

                                            (
                                                ref_power,
                                                tile_power,
                                                alt,
                                                az,
                                                times,
                                            ) = sat_data

                                            # Altitude is in deg while az is in radians
                                            # convert alt to radians
                                            # za - zenith angle
                                            alt = np.radians(alt)
                                            za = np.pi / 2 - alt
                                            az = np.asarray(az)

                                            # Now convert to healpix coordinates
                                            # healpix_index = hp.ang2pix(nside,θ, ɸ)
                                            healpix_index = hp.ang2pix(nside, za, az)

                                            # multiple data points fall within a single healpix pixel
                                            # find the unique pixels
                                            u = np.unique(healpix_index)

                                            ref_pass = np.array(
                                                [
                                                    np.nanmean(
                                                        ref_power[
                                                            np.where(
                                                                healpix_index == i
                                                            )[0]
                                                        ]
                                                    )
                                                    for i in u
                                                ]
                                            )
                                            tile_pass = np.array(
                                                [
                                                    np.nanmean(
                                                        tile_power[
                                                            np.where(
                                                                healpix_index == i
                                                            )[0]
                                                        ]
                                                    )
                                                    for i in u
                                                ]
                                            )
                                            times_pass = np.array(
                                                [
                                                    np.mean(
                                                        times[
                                                            np.where(healpix_index == i)
                                                        ][0]
                                                    )
                                                    for i in u
                                                ]
                                            )
                                            ref_fee_pass = np.array(
                                                [rotated_fee[i] for i in u]
                                            )
                                            mwa_fee_pass = np.array(
                                                [mwa_fee[i] for i in u]
                                            )

                                            # implement RFE gain corrections here
                                            rfe_polyfit = np.load(rfe_gain)
                                            gain_cal = np.poly1d(rfe_polyfit)
                                            # rfe_thresh = gain_cal.roots[0]
                                            rfe_thresh = max(gain_cal.roots)
                                            tile_pass_rfe = [
                                                i + gain_cal(i)
                                                if i >= rfe_thresh
                                                else i
                                                for i in tile_pass
                                            ]

                                            # magic here
                                            # the beam shape finally emerges
                                            # mwa_pass = np.array(tile_pass) - np.array(ref_pass) + np.array(ref_fee_pass)
                                            mwa_pass = (
                                                np.array(tile_pass_rfe)
                                                - np.array(ref_pass)
                                                + np.array(ref_fee_pass)
                                            )

                                            # fit the power level of the pass to the mwa_fee model using a single gain value
                                            offset = fit_gain(
                                                map_data=mwa_pass, fee=mwa_fee_pass
                                            )

                                            mwa_pass_fit = mwa_pass - offset[0]

                                            if mwa_pass_fit.size != 0:

                                                # determine how well the data fits the model with chi-square
                                                pval = fit_test(
                                                    map_data=mwa_pass_fit,
                                                    fee=mwa_fee_pass,
                                                )

                                                if plots == "True":
                                                    mwa_pass_raw = (
                                                        np.array(tile_pass)
                                                        - np.array(ref_pass)
                                                        + np.array(ref_fee_pass)
                                                    )
                                                    offset = fit_gain(
                                                        map_data=mwa_pass_raw,
                                                        fee=mwa_fee_pass,
                                                    )
                                                    mwa_pass_fit_raw = (
                                                        mwa_pass_raw - offset[0]
                                                    )

                                                    plt_fee_fit(
                                                        times_pass,
                                                        mwa_fee_pass,
                                                        mwa_pass_fit,
                                                        mwa_pass_fit_raw,
                                                        f"{out_dir}/fit_plots/{tile}_{ref}/",
                                                        point,
                                                        timestamp,
                                                        sat,
                                                    )

                                                # a goodness of fit threshold
                                                if pval >= 0.8:

                                                    # loop though all healpix pixels for the pass
                                                    for i in range(len(u)):

                                                        tile_data["mwa_maps"][
                                                            f"{point}"
                                                        ][u[i]].append(mwa_pass_fit[i])
                                                        tile_data["ref_maps"][
                                                            f"{point}"
                                                        ][u[i]].append(ref_pass[i])
                                                        tile_data["tile_maps"][
                                                            f"{point}"
                                                        ][u[i]].append(tile_pass[i])
                                                        tile_data["times"][f"{point}"][
                                                            u[i]
                                                        ].append(times_pass[i])
                                                        tile_data["sat_map"][
                                                            f"{point}"
                                                        ][u[i]].append(sat)

                else:
                    print(f"Missing {ref}_{tile}_{timestamp}_aligned.npz")
                    continue

    # Sort data by satellites

    # list of all possible satellites
    sat_ids = list(norad_ids.values())

    # create a dictionary, with the keys being sat_ids and the values being healpix maps of data from those sats
    # Fist level keys are pointings with dictionaty values
    # Second level keys are satellite ids with healpix map lists
    mwa_sat_data = {}
    ref_sat_data = {}
    tile_sat_data = {}
    time_sat_data = {}

    # loop over pointings for all maps
    for p in pointings:

        mwa_map = np.asarray(tile_data["mwa_maps"][p])
        tile_map = np.asarray(tile_data["tile_maps"][p])
        ref_map = np.asarray(tile_data["ref_maps"][p])
        sat_map = np.asarray(tile_data["sat_map"][p])
        time_map = np.asarray(tile_data["times"][p])

        mwa_sat_data[p] = {}
        ref_sat_data[p] = {}
        tile_sat_data[p] = {}
        time_sat_data[p] = {}

        # loop over all sats
        for s in sat_ids:

            mwa_sat_data[p][s] = []
            ref_sat_data[p][s] = []
            tile_sat_data[p][s] = []
            time_sat_data[p][s] = []

            # loop over every healpix pixel
            for i in range(len(ref_map)):

                # Find subset of data for each sat
                sat_idx = np.where(np.asarray(sat_map[i]) == s)
                mwa_sat_data[p][s].append((np.asarray(mwa_map[i])[sat_idx]).tolist())
                ref_sat_data[p][s].append((np.asarray(ref_map[i])[sat_idx]).tolist())
                tile_sat_data[p][s].append((np.asarray(tile_map[i])[sat_idx]).tolist())
                time_sat_data[p][s].append((np.asarray(time_map[i])[sat_idx]).tolist())

    # Save map arrays to npz file
    tile_sat_data = {
        "mwa_map": mwa_sat_data,
        "ref_map": ref_sat_data,
        "tile_map": tile_sat_data,
        "time_map": time_sat_data,
    }
    np.savez_compressed(f"{out_dir}/{tile}_{ref}_sat_maps.npz", **tile_sat_data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="""
        Project a sat pass onto a healpix map using ephemeris data
        """
    )

    parser.add_argument(
        "--align_dir",
        metavar="\b",
        default="../../outputs/align_data/",
        help="Dir where agligned data date is saved. Default:../../outputs/align_data",
    )

    parser.add_argument(
        "--out_dir",
        metavar="\b",
        default="./../../outputs/tile_maps/tile_maps_raw/",
        help="Output directory. Default=./../../outputs/tile_maps/tile_maps_raw/",
    )

    parser.add_argument(
        "--obs_point",
        metavar="\b",
        default="../../outputs/beam_pointings/obs_pointings.json",
        help="Observation pointing lists. Default=../../outputs/beam_pointings/obs_pointings.json",
    )

    parser.add_argument(
        "--chrono_dir",
        metavar="\b",
        default="./../../outputs/sat_ephemeris/chrono_json",
        help="Output directory. Default=./../../outputs/sat_ephemeris/chrono_json/",
    )

    parser.add_argument(
        "--map_dir",
        metavar="\b",
        default="../../outputs/sat_channels/window_maps/",
        help="Satellite channel map. Default=../../outputs/sat_channels/window_maps/",
    )

    parser.add_argument(
        "--ref_model",
        metavar="\b",
        default="../../outputs/reproject_ref/ref_dipole_models.npz",
        help="Healpix reference FEE model file. default=../../outputs/reproject_ref/ref_dipole_models.npz",
    )

    parser.add_argument(
        "--rfe_gain",
        metavar="\b",
        default="../../outputs/tile_maps/rfe_gain/rfe_gain_fit.npy",
        help="RF Explorer gain fit. default=../../outputs/tile_maps/rfe_gain/rfe_gain_fit.npy",
    )

    parser.add_argument(
        "--fee_map",
        metavar="\b",
        default="../../outputs/tile_maps/FEE_maps/mwa_fee_beam.npz",
        help="Healpix FEE map of mwa tile. default=../../outputs/tile_maps/FEE_maps/mwa_fee_beam.npz",
    )

    parser.add_argument(
        "--fee_map_flagged",
        metavar="\b",
        default="../../outputs/tile_maps/FEE_maps/mwa_fee_beam_9_flagged.npz",
        help="Healpix FEE map of mwa tile. default=../../outputs/tile_maps/FEE_maps/mwa_fee_beam_9_flagged.npz",
    )

    parser.add_argument(
        "--fit_thresh",
        metavar="\b",
        default=0.9,
        help="Goodness of fit threshold. 0.9 seems to only reject obvious outliers",
    )
    parser.add_argument(
        "--noi_thresh",
        metavar="\b",
        type=int,
        default=3,
        help="Noise Threshold: Multiples of MAD. Default=3.",
    )
    parser.add_argument(
        "--sat_thresh",
        metavar="\b",
        type=int,
        default=1,
        help="σ threshold to detect sats Default=1.",
    )
    parser.add_argument(
        "--pow_thresh",
        metavar="\b",
        type=int,
        default=5,
        help="Power Threshold to detect sats. Default=5 dB.",
    )
    parser.add_argument(
        "--nside",
        metavar="\b",
        type=int,
        default=32,
        help="Healpix Nside. Default = 32",
    )
    parser.add_argument(
        "--plots",
        metavar="\b",
        default=False,
        help="If True, create a gazzillion plots for each sat pass. Default = False",
    )
    parser.add_argument(
        "--start_date",
        metavar="\b",
        help="Date from which to start aligning data. Ex: 2019-10-10",
    )
    parser.add_argument(
        "--stop_date",
        metavar="\b",
        help="Date until which to align data. Ex: 2019-10-11",
    )

    args = parser.parse_args()

    start_date = args.start_date
    stop_date = args.stop_date
    obs_point = args.obs_point
    noi_thresh = args.noi_thresh
    sat_thresh = args.sat_thresh
    pow_thresh = args.pow_thresh
    fit_thresh = args.fit_thresh
    nside = args.nside
    plots = args.plots
    ref_model = args.ref_model
    rfe_gain = args.rfe_gain
    fee_map = args.fee_map
    fee_map_flagged = args.fee_map_flagged

    align_dir = Path(args.align_dir)
    chrono_dir = Path(args.chrono_dir)
    out_dir = Path(args.out_dir)
    map_dir = Path(args.map_dir)

    # Tile names
    refs = tile_names()[:4]
    tiles = tile_names()[4:]

    # All relevant tile pairs
    tile_pairs = []
    for ref in refs:
        if "XX" in ref:
            for tile in [t for t in tiles if "XX" in t]:
                tile_pairs.append([ref, tile])
        else:
            for tile in [t for t in tiles if "YY" in t]:
                tile_pairs.append([ref, tile])

    # Read observation pointing list
    with open(obs_point) as point:
        obs_p = json.load(point)
        point_0 = obs_p["point_0"]
        point_2 = obs_p["point_2"]
        point_4 = obs_p["point_4"]
        point_41 = obs_p["point_41"]

    # dates: list of days
    # date_time = list of 30 min observation windows
    dates, date_time = time_tree(start_date, stop_date)

    # Save logs
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    sys.stdout = open(f"{out_dir}/logs_{start_date}_{stop_date}.txt", "a")

    #    project_tile_healpix(tile_pairs[0])
    #    project_tile_healpix(['rf0YY', 'S33YY'])

    # Parallization magic happens here
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(project_tile_healpix, tile_pairs)
