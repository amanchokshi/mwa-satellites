"""
Beam Utils
----------

A set of tools used to create and visualize tile maps

"""

import healpy as hp
import numpy as np
from numpy.polynomial import polynomial as poly
from scipy.stats import median_absolute_deviation as mad


# rotate func written by Jack Line
def rotate_map(nside, angle=None, healpix_array=None, savetag=None, flip=False):
    """Rotates healpix array by the desired angle, and saves it.

    Optionally flip the data, changes east-west into west-east because astronomy

    :param nside: Healpix nside
    :param angle: Angle by which to rotate the healpix map
    :param healpix_array: Input healpix array to be rotated
    :param savetag: If given, will save the rotated beam map to :samp:`.npz` file
    :param flip: Do an astronomy coordinate flip, if True

    :returns:
        - Rotated healpix map

    """

    # theta phi values of each pixel
    hp_indices = np.arange(hp.nside2npix(nside))
    θ, ɸ = hp.pix2ang(nside, hp_indices)

    new_hp_inds = hp.ang2pix(nside, θ, ɸ + angle)

    # Flip the data to match astro conventions
    if flip is True:
        new_angles = []
        for phi in ɸ:
            if phi <= np.pi:
                new_angles.append(np.pi - phi)
            else:
                new_angles.append(3 * np.pi - phi)
        new_hp_inds = hp.ang2pix(nside, ɸ, np.asarray(new_angles))

    # Save the array in the new order
    if savetag:
        np.savez_compressed(savetag, beammap=healpix_array[new_hp_inds])

    return healpix_array[new_hp_inds]


def healpix_cardinal_indices(nside, za_max=90):
    """Cardinal slices of healpix maps, upto an zenith angle threshold.

    Healpix maps of nside=32 do not have pixels along their cardinal axes, but do have them along their diagonal axes. This function
    determined the indices of diagonal slices of healpix maps, assuming the original map has been rotated by + 𝛑/4 using the
    :func:`~embers.tile_maps.beam_utils.rotate_map` function.

    :param nside: Healpix nside
    :param za_max: Maximum zenith angle, default: 90 (horizon)

    :returns:
        - :class:`~tuple` of NS, EW healpix indices

    """

    # theta phi values of each pixel
    hp_indices = np.arange(hp.nside2npix(nside))
    θ, ɸ = hp.pix2ang(nside, hp_indices)

    # healpix indices above the horizon
    above_horizon_indices = np.where(θ <= np.radians(za_max))[0]

    # pixel coords above the horizon
    ɸ_above_horizon = ɸ[above_horizon_indices]

    NS_indices = []
    EW_indices = []

    # pixel indices along N, E, S, W slices
    # order the indices such that they proceed from N -> S or E -> W
    n_slice = sorted(
        np.where((np.round(np.degrees(ɸ_above_horizon))) == 45)[0], reverse=True
    )
    e_slice = sorted(
        np.where((np.round(np.degrees(ɸ_above_horizon))) == 135)[0], reverse=True
    )
    s_slice = sorted(np.where((np.round(np.degrees(ɸ_above_horizon))) == 225)[0])
    w_slice = sorted(np.where((np.round(np.degrees(ɸ_above_horizon))) == 315)[0])

    NS_indices.extend(n_slice)
    NS_indices.extend(s_slice)
    EW_indices.extend(e_slice)
    EW_indices.extend(w_slice)

    return (NS_indices, EW_indices)


def healpix_cardinal_slices(nside, hp_map, za_max):
    """Slice healpix map along NS, EW axes, assuming it has been rotated by + 𝛑/4.

    :param nside: Healpix nside
    :param hp_map: Healpix imput data map
    :param za_max: Maximum zenith angle

    :returns:
        - :class:`~tuple` of NS, EW data slices of the imput healpix map, each of which contain the healpix indices and corresponding zenith angles
    """

    NS_indices, EW_indices, _ = healpix_cardinal_indices(nside, za_max=za_max)

    θ_NS, ɸ_NS = np.degrees(hp.pix2ang(nside, NS_indices))
    θ_EW, ɸ_EW = np.degrees(hp.pix2ang(nside, EW_indices))

    zenith_angle_NS = []
    for i, j in zip(θ_NS, ɸ_NS):
        if j <= 180:
            zenith_angle_NS.append(-1 * i)
        else:
            zenith_angle_NS.append(i)

    zenith_angle_EW = []
    for i, j in zip(θ_EW, ɸ_EW):
        if j <= 180:
            zenith_angle_EW.append(-1 * i)
        else:
            zenith_angle_EW.append(i)

    NS_data = [hp_map[NS_indices], zenith_angle_NS]
    EW_data = [hp_map[EW_indices], zenith_angle_EW]

    return (NS_data, EW_data)


def nan_mad(good_ref_map):
    """Compute MAD of values in pixel of healpix map while ignoring nans.

    :param good_ref_map: Reference healpix map, output from :func:`~embers.tile_maps.beam_utils.good_ref_maps`

    :returns:
        - ref_map_mad - Median Absolute Deviation of the input healpix map pixels

    """

    ref_map_mad = []
    for j in good_ref_map:
        if j != []:
            j = np.asarray(j)
            j = j[~np.isnan(j)]
            ref_map_mad.append(mad(j))
        else:
            ref_map_mad.append(np.nan)

    ref_map_mad = np.asarray(ref_map_mad)
    ref_map_mad[np.where(ref_map_mad == np.nan)] = np.nanmean(ref_map_mad)

    return ref_map_mad


def map_slices(nside, good_map, za_max):
    """Slice healpix map along NS & EW axes returning Median and MAD arrays of the cardinal slices.

    :param nside: Healpix nside
    :param good_map: Healpix map, with pixels having distribution of values in lists
    :param za_max: Maximum zenith angle

    :returns:
        - :class:`~tuple` of NS & EW data, with each being a list of Median, MAD and Zenith angle arrays for the given cardianl slice of the healpix map

    """

    ref_map_NS, ref_map_EW = healpix_cardinal_slices(
        nside, np.asarray(good_map), za_max
    )

    NS_med_map = np.asarray(
        [(np.nanmedian(i) if i != [] else np.nan) for i in ref_map_NS[0]]
    )
    NS_mad_map = np.asarray(nan_mad(ref_map_NS[0]))
    za_NS = ref_map_NS[1]

    EW_med_map = np.asarray(
        [(np.nanmedian(i) if i != [] else np.nan) for i in ref_map_EW[0]]
    )
    EW_mad_map = np.asarray(nan_mad(ref_map_EW[0]))
    za_EW = ref_map_EW[1]

    NS_data = [NS_med_map, NS_mad_map, za_NS]
    EW_data = [EW_med_map, EW_mad_map, za_EW]

    return (NS_data, EW_data)


def poly_fit(x, y, data, order):
    """Fit polynominal of any order to data

    :param x: Data array
    :param y: Data array
    :param y: Array of same size as x, y, but with nan's which can be used to mask x,y
    :param order: Degree of polynominal fit

    """

    x = np.asarray(x)
    y = np.asarray(y)

    bad_values = np.isnan(data)
    x_good = x[~bad_values]
    y_good = y[~bad_values]
    coefs = poly.polyfit(x_good, y_good, order)
    fit = poly.polyval(x, coefs)

    return fit


def plot_healpix(
    data_map=None,
    fig=None,
    sub=None,
    title=None,
    vmin=None,
    vmax=None,
    cmap=None,
    cbar=True,
):
    """Yeesh do some healpix magic to plot the thing

    :param data_map: Healpix input map to plot
    :param fig: Figure number to use
    :param sub: Matplotlib subplot syntax
    :param title: Plot title
    :param vmin: Colormap minimum
    :param vmax: Colormap maximum
    :param cmap: Matplotlib :class:`~matplotlib.colors.ListedColormap`
    :param cbar: If True, plot a colorbar

    :returns:
        - Plot of healpix map

    """

    # Disable cryptic healpy warnings. Can't figure out where they originate
    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)

    hp.delgraticules()
    hp.orthview(
        map=data_map,
        coord="E",
        fig=fig,
        half_sky=True,
        rot=(0, 90, 180),
        xsize=1200,
        title=title,
        sub=sub,
        min=vmin,
        max=vmax,
        cmap=cmap,
        notext=True,
        hold=True,
        cbar=cbar,
        return_projected_map=False,
    )

    hp.graticule(dpar=10, coord="E", color="k", alpha=0.7, dmer=45, lw=0.4, ls=":")

    # Altitude grid
    hp.projtext(
        00.0 * (np.pi / 180.0),
        225.0 * (np.pi / 180),
        "0",
        color="k",
        coord="E",
        fontsize=6,
        fontweight="light",
    )
    hp.projtext(
        30.0 * (np.pi / 180.0),
        225.0 * (np.pi / 180),
        "30",
        color="k",
        coord="E",
        fontsize=6,
        fontweight="light",
    )
    hp.projtext(
        60.0 * (np.pi / 180.0),
        225.0 * (np.pi / 180),
        "60",
        color="k",
        coord="E",
        fontsize=6,
        fontweight="light",
    )

    # NSEW
    hp.projtext(
        80.0 * (np.pi / 180.0),
        000.0 * (np.pi / 180.0),
        r"$N  $",
        coord="E",
        color="w",
        fontweight="light",
        verticalalignment="top",
    )
    hp.projtext(
        80.0 * (np.pi / 180.0),
        090.0 * (np.pi / 180.0),
        r"$E  $",
        coord="E",
        color="w",
        fontweight="light",
        horizontalalignment="right",
    )
    hp.projtext(
        80.0 * (np.pi / 180.0),
        180.0 * (np.pi / 180.0),
        r"$S  $",
        coord="E",
        color="w",
        fontweight="light",
        verticalalignment="bottom",
    )
    hp.projtext(
        80.0 * (np.pi / 180.0),
        270.0 * (np.pi / 180.0),
        r"$W  $",
        coord="E",
        color="w",
        fontweight="light",
        horizontalalignment="left",
    )
