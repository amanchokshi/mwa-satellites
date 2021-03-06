"""
Chronological Ephemeris
-----------------------

Collate ephemeris data generated by :mod:`~embers.sat_utils.sat_ephemeris` for multiple satellites
and determine all ephemeris present in 30 minute observation windows.

"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytz
from scipy import interpolate


def obs_times(time_zone, start_date, stop_date):
    """Time conversion tools for 30 minute observations

    Given a :samp:`time_zone`, :samp:`start_date`, :samp:`stop_date`,
    create lists of human readable start times in :samp:`YYYY-MM-DD-HH:MM`
    format, and start and stop UNIX times for 30 minute rf observations.

    .. code-block:: python

        from embers.sat_utils.chrono_ephem import obs_times
        time_tuple = obs_times("Australia/Perth", "2020-01-01", "2020-01-02")
        obs_time, obs_unix, obs_unix_end - time_tuple

        print(obs_time)
        >>> ["2020-01-01-00:00", "2020-01-01-00:30", ....]

        print(obs_unix)
        >>> [1577809800.0, 1577811600.0, 1577813400.0, ...]

        print(obs_unix_end)
        >>> [1577809800.0, 1577811600.0, 1577813400.0, ...]

    :param time_zone: A :class:`~str` representing a :samp:`pytz` `timezones <https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568>`_.
    :param start_date: in :samp:`YYYY-MM-DD` format :class:`~str`
    :param stop_date: in :samp:`YYYY-MM-DD` format :class:`~str`

    :returns:
        A :class:`~tuple` (obs_time, obs_unix, obs_unix_end)

        - obs_time: :class:`~list` of start times of 30 min observations in :samp:`YYYY-MM-DD-HH::MM` format
        - obs_unix: :class:`~list` of start times of 30 min observations in unix time
        - obs_unix_end: :class:`~list` of end times of 30 min observations in unix time

    """

    # Time stuff
    # The time input is in local time. As in Austraila/Perth
    local = pytz.timezone(time_zone)

    t_start = datetime.strptime(start_date, "%Y-%m-%d")
    t_stop = datetime.strptime(stop_date, "%Y-%m-%d")

    # Number of days that the date range spans
    n_days = (t_stop - t_start).days

    # YYYY-MM-DD-HH:MM format
    obs_time = []

    # Start of half hour obs in unix time
    obs_unix = []

    # End of half hour obs in unix time
    obs_unix_end = []

    # The +1 makes the date ranges inclusive
    for i in range(n_days + 1):
        day = t_start + timedelta(days=i)
        date = day.strftime("%Y-%m-%d")

        # loop over 48x30 minute obs in a day
        for j in range(48):
            t_delta = datetime.strptime(date, "%Y-%m-%d") + timedelta(minutes=30 * j)
            # convert t_delta to a readable string YYYY-MM-DD-HH:MM
            d_time = t_delta.strftime("%Y-%m-%d-%H:%M")

            # Convert from naive local time to utc aware time
            utc_delta = local.localize(t_delta, is_dst=None).astimezone(pytz.utc)

            # convert to a unix timestamp, used within rf explorer data files
            utc_unix = utc_delta.timestamp()
            # time at end of half hour window
            utc_unix_end = utc_unix + (30 * 60)

            obs_time.append(d_time)
            obs_unix.append(utc_unix)
            obs_unix_end.append(utc_unix_end)

    return (obs_time, obs_unix, obs_unix_end)


def interp_ephem(t_array, s_alt, s_az, interp_type, interp_freq):
    """Interpolates satellite ephemeris from :mod:`~embers.sat_utils.sat_ephemeris`

    Satellite ephemeris is interpolated to the same freq as used in :mod:`~embers.rf_tools.align_data`.
    This ensures that each point of rf data, will have an corresponding ephemeris.
    :samp:`Time`, :samp:`Altitude` & :samp:`Azimuth` ephemeris arrays are interpolated.

    :param t_array: Time array of on satellite pass :class:`~numpy.ndarray`
    :param s_alt: Satellite :samp:`Altitude` at the :samp:`t_array` :class:`~numpy.ndarray`
    :param s_az: Satellite :samp:`Azimuth` at the :samp:`t_array` :class:`~numpy.ndarray`
    :param interp_type: Type of interpolation. Ex: :samp:`cubic`, :samp:`linear` :class:`str`
    :param interp_freq: Frequency at which to interpolate, in Hertz. :class:`~int`

    :returns:
        A :class:`~tuple` (time_interp, sat_alt, sat_az)

        - time_interp: Interpolated :samp:`t_array`
        - sat_alt: Interpolated :samp:`s_alt`
        - sat_az: Interpolated :samp:`s_az`

    """

    # Create interpolation functions. Math functions, not Python!
    alt_interp = interpolate.interp1d(t_array, s_alt, kind=interp_type)

    # The next step was a bit tricky. Azimuth may wrap around.
    # This may lead to a discontinuity between 0, 2π
    # We deal with this, by unwrapping the angles

    # This extends the angles beyond 2π, if the angles cross the discontinuity
    s_az_cont = np.unwrap(s_az)
    az_interp = interpolate.interp1d(t_array, s_az_cont, kind=interp_type)

    # Makes start and end times clean integers
    # Also ensures that the interp range is inclusive of data points
    start = math.ceil(t_array[0])
    stop = math.floor(t_array[-1])

    # Create time array, at which to evaluate alt/az of sat
    time_interp = list(np.double(np.arange(start, stop, (1 / interp_freq))))

    sat_alt = list(alt_interp(time_interp))

    # The modulus division by 2π, un-does the np.unwrap
    sat_az = list(az_interp(time_interp) % (2 * np.pi))

    return (time_interp, sat_alt, sat_az)


def write_json(data, filename=None, out_dir=None):
    """writes data to json file in output dir

    :param data: Data to be written to json file
    :param filename: Json filename :class:`~str`
    :param out_dir: Path to output directory :class:`~str`

    """

    with open(f"{out_dir}/{filename}", "w") as f:
        json.dump(data, f, indent=4)


def save_chrono_ephem(
    time_zone, start_date, stop_date, interp_type, interp_freq, ephem_dir, out_dir
):
    """Save 30 minute ephem from all satellites to file.

    Native skyfiled gps timestamps are converted to unix
    timestamps to match the output of the rf explorers. The
    alt, az data is interpolated to match the cadence of
    :mod:`~embers.rf_tools.align_data`. Make a json file with all the passes
    from each 30 min observation. This will help in the
    next stage, where we identify all sats in each obs.

    :param time_zone: A :class:`~str` representing a :samp:`pytz` `timezones <https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568>`_.
    :param start_date: in :samp:`YYYY-MM-DD` format :class:`~str`
    :param stop_date: in :samp:`YYYY-MM-DD` format :class:`~str`
    :param interp_type: Type of interpolation. Ex: :samp:`cubic`, :samp:`linear` :class:`str`
    :param interp_freq: Frequency at which to interpolate, in Hertz. :class:`~int`
    :param ephem_dir: Directory where :samp:`npz` ephemeris files from :func:`~embers.sat_utils.sat_ephemeris.save_ephem` are saved :class:`~str`
    :param out_dir: Path to output directory where chronological ephemeris files will be saved :class:`~str`

    """

    obs_time, obs_unix, obs_unix_end = obs_times(time_zone, start_date, stop_date)

    # creates output dir, if it doesn't exist
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Lets make the a json file for each 30 min observation, with an empty list
    data = []
    for i in range(len(obs_time)):
        write_json(data, filename=f"{obs_time[i]}.json", out_dir=out_dir)

    # Finds all sat ephem json files, and loops over them
    for ephem_npz in list(Path(ephem_dir).glob("*.npz")):

        # Extract data from npz ephem file
        sat_ephem = np.load(ephem_npz, allow_pickle=True)
        t_array = sat_ephem["time_array"]
        s_alt = sat_ephem["sat_alt"]
        s_az = sat_ephem["sat_az"]
        s_id = str(sat_ephem["sat_id"])

        # here, we're looping over each satellite pass with a single sat ephem file
        # to check which observation window it falls in
        for pass_idx in range(len(t_array)):

            # if sat ephem has more than 10 data points
            if t_array[pass_idx].shape[0] >= 10:

                time_interp, sat_alt, sat_az = interp_ephem(
                    t_array[pass_idx],
                    s_alt[pass_idx],
                    s_az[pass_idx],
                    interp_type,
                    interp_freq,
                )

                # Find which sat passes are within a 30 minute obs
                for obs_int in range(len(obs_unix)):

                    sat_ephem = {}
                    sat_ephem["sat_id"] = [s_id]
                    sat_ephem["time_array"] = []
                    sat_ephem["sat_alt"] = []
                    sat_ephem["sat_az"] = []

                    # Case I: Satpass occurs completely within the 30min observation
                    if (
                        obs_unix[obs_int] < time_interp[0]
                        and obs_unix_end[obs_int] > time_interp[-1]
                    ):

                        # append the whole pass to the dict
                        sat_ephem["time_array"].extend(time_interp)
                        sat_ephem["sat_alt"].extend(sat_alt)
                        sat_ephem["sat_az"].extend(sat_az)

                    # Case II: Satpass begins before the obs, but ends within it
                    elif (
                        obs_unix[obs_int] > time_interp[0]
                        and obs_unix[obs_int] < time_interp[-1]
                        and obs_unix_end[obs_int] > time_interp[-1]
                    ):

                        # find index of time_interp == obs_unix
                        start_idx = (
                            np.where(np.asarray(time_interp) == obs_unix[obs_int])
                        )[0][0]

                        # append the end of the pass which is within the obs
                        sat_ephem["time_array"].extend(time_interp[start_idx:])
                        sat_ephem["sat_alt"].extend(sat_alt[start_idx:])
                        sat_ephem["sat_az"].extend(sat_az[start_idx:])

                    # Case III: Satpass begins within the obs, but ends after it
                    elif (
                        obs_unix_end[obs_int] > time_interp[0]
                        and obs_unix_end[obs_int] < time_interp[-1]
                        and obs_unix[obs_int] < time_interp[0]
                    ):

                        # find index of time_interp == obs_unix_end
                        stop_idx = (
                            np.where(np.asarray(time_interp) == obs_unix_end[obs_int])
                        )[0][0]

                        # append the end of the pass which is within the obs
                        sat_ephem["time_array"].extend(time_interp[: stop_idx + 1])
                        sat_ephem["sat_alt"].extend(sat_alt[: stop_idx + 1])
                        sat_ephem["sat_az"].extend(sat_az[: stop_idx + 1])

                    # doesn't create json if there are no satellite passes within it
                    if sat_ephem["time_array"] != []:

                        print(f"Satellite {s_id} in {obs_time[obs_int]}")

                        # open the relevant json file and loads contents to 'data_json'
                        with open(f"{out_dir}/{obs_time[obs_int]}.json") as json_file:
                            data_json = json.load(json_file)

                            # append new satpass ephem data to data_json
                            data_json.append(sat_ephem)

                            # write the combined data back to the original file
                            write_json(
                                data_json,
                                filename=f"{obs_time[obs_int]}.json",
                                out_dir=out_dir,
                            )

                            # clear data_json
                            data_json = []
