import sys
import json
import argparse
import numpy as np
import healpy as hp
from pathlib import Path
import concurrent.futures
import matplotlib.pyplot as plt
from scipy.stats import median_absolute_deviation as mad
from sat_channels import time_tree, time_filter,center_of_gravity
from channels_plt import plt_waterfall_pass, plt_channel_basic, sat_plot

# Custom spectral colormap
sys.path.append('../decode_rf_data')
from colormap import spectral
cmap = spectral()


def read_aligned(ali_file=None):
    '''Read aligned data npz file'''
    paired_data = np.load(ali_file, allow_pickle=True)
    
    power   = paired_data['ref_p_aligned']
    times   = paired_data['time_array']

    return [power, times]


def noise_floor(sat_thresh, noi_thresh, data=None):
    '''Computes '''
    
    # compute the standard deviation of data, and use it to identify occupied channels
    σ = np.std(data)
    
    # Any channel with a max power >= σ has a satellite
    sat_cut = sat_thresh*σ
    chans_pow_max = np.amax(data, axis=0)
    
    # Exclude the channels with sats, to only have noise data
    noise_chans = np.where(chans_pow_max < sat_cut)[0]
    noise_data = data[:, noise_chans]
    
    # noise median, noise mad, noise threshold = μ + 3*σ
    μ_noise = np.median(noise_data)
    σ_noise = mad(noise_data, axis=None)
    # because we rescale power to have zero median
    noise_threshold = (μ_noise-μ_noise) + noi_thresh*σ_noise
    
    # scale the data so that it has zero median
    data = data - μ_noise
    
    return (data, noise_threshold)


def power_ephem(
        ref_file,
        chrono_file,
        sat_id,
        date,
        timestamp
        ):

    '''Create power, alt, az arrays at constant cadence'''

    power, times = read_aligned(ali_file=ref_file)

    # Scale noise floor to zero and determine noise threshold
    power, noise_threshold = noise_floor(sat_thresh, noi_thresh, power)

    with open(chrono_file) as chrono:
        chrono_ephem = json.load(chrono)
    
        norad_list = [chrono_ephem[s]["sat_id"][0] for s in range(len(chrono_ephem))]
        
        norad_index = norad_list.index(sat_id)

        norad_ephem = chrono_ephem[norad_index]
            
        rise_ephem  = norad_ephem["time_array"][0] 
        set_ephem   = norad_ephem["time_array"][-1]
        sat_alt     = norad_ephem["sat_alt"]

        if max(sat_alt) >= alt_thresh:
        
            intvl = time_filter(rise_ephem, set_ephem, np.asarray(times))
            
            if intvl != None:
                
                w_start, w_stop = intvl
                
                window_len = w_stop - w_start + 1
                
                # Slice [crop] the power/times arrays to the times of sat pass
                power_c = power[w_start:w_stop+1, :]
                times_c = times[w_start:w_stop+1]

                possible_chans = []
                occu_list = []
                
                # Loop over every channel
                for s_chan in range(len(power_c[0])):
                    
                    channel_power = power_c[:, s_chan]
                    
                    # Percentage of signal occupancy above noise threshold
                    window_occupancy = (np.where(channel_power >= noise_threshold))[0].size/window_len
                
                    max_s = np.amax(channel_power)
                    min_s = np.amin(channel_power)

                    # Arbitrary threshold below which satellites aren't counted
                    # Only continue if there is signal for more than 80% of satellite pass
                    if (max(channel_power) >= pow_thresh and 
                            occ_thresh <= window_occupancy < 1.00):

                        if (times[0] == times_c[0]):
                            if (all(p < noise_threshold for p in channel_power[-11:-1])) is True:
                                occu_list.append(window_occupancy)
                                possible_chans.append(s_chan)
                                #print(f'{sat_id}: {s_chan} {window_occupancy}')
                                
                                if plots == 'True':
                                    plt_channel_basic(
                                            f'{plt_dir}/{date}/{timestamp}', times_c, channel_power,
                                            s_chan, min_s, 32, noise_threshold,
                                            pow_thresh, sat_id, timestamp)

                        elif (times[-1] == times_c[-1]):
                            if (all(p < noise_threshold for p in channel_power[:10])) is True:
                                occu_list.append(window_occupancy)
                                possible_chans.append(s_chan)
                                #print(f'{sat_id}: {s_chan} {window_occupancy}')
                    
                                if plots == 'True':
                                    plt_channel_basic(
                                            f'{plt_dir}/{date}/{timestamp}', times_c, channel_power,
                                            s_chan, min_s, 32, noise_threshold,
                                            pow_thresh, sat_id, timestamp)

                        else:
                            if (all(p < noise_threshold for p in channel_power[:10]) and 
                                all(p < noise_threshold for p in channel_power[-11:-1])) is True:
                                occu_list.append(window_occupancy)
                                possible_chans.append(s_chan)
                                #print(f'{sat_id}: {s_chan} {window_occupancy}')
                    
                                if plots == 'True':
                                    plt_channel_basic(
                                            f'{plt_dir}/{date}/{timestamp}', times_c, channel_power,
                                            s_chan, min_s, 32, noise_threshold,
                                            pow_thresh, sat_id, timestamp)
                        
                
                
                # If channels are identified in the 30 min obs
                n_chans = len(possible_chans)

                if n_chans > 0:
                    
                    # The most lightly channel is one with the highest occupation
                    good_chan = possible_chans[occu_list.index(max(occu_list))]
                    
                    if plots == 'True':
                        plt_waterfall_pass(
                                power, sat_id, w_start, w_stop, timestamp, cmap, 
                                chs=possible_chans, good_ch=good_chan, out_dir=f'{plt_dir}/{date}/{timestamp}', )
                    
                    return good_chan

                else:
                    if plots == 'True':
                        plt_waterfall_pass(
                                power, sat_id, w_start, w_stop, timestamp, cmap, 
                                chs=None, good_ch=None, out_dir=f'{plt_dir}/{date}/{timestamp}', )
                    return 0

            else:
                return 0

        else:
            return 0


def window_chan_map(obs_stamp):

    date, timestamp = obs_stamp

    if plots == 'True':
        Path(f'{plt_dir}/{date}/{timestamp}').mkdir(parents=True, exist_ok=True)
    
    channel_map = {}

    ref_file = f'{ali_dir}/{date}/{timestamp}/rf0XX_S07XX_{timestamp}_aligned.npz'
    chrono_file = f'{chrono_dir}/{timestamp}.json'
    
    try:
        Path(ref_file).is_file()

        with open(chrono_file) as chrono:
            chrono_ephem = json.load(chrono)

            if chrono_ephem != []:
        
                norad_list = [chrono_ephem[s]["sat_id"][0] for s in range(len(chrono_ephem))]

                if norad_list != []:
                
                    for sat in norad_list:

                        sat_data = power_ephem(
                                ref_file,
                                chrono_file,
                                sat,
                                date,
                                timestamp
                                )
                       
                        if sat_data != 0:
                            sat_chan = sat_data
                            
                            channel_map[f'{sat}'] = sat_chan

    
    except Exception as e:
        print(e)
        # Exception message is forwarded from ../decode_rf_data/rf_data.py

    # Save channel map
    with open(f'{out_dir}/window_maps/{timestamp}.json','w') as f: 
        json.dump(channel_map, f, indent=4) 


        
if __name__=='__main__':

    parser = argparse.ArgumentParser(description="""
        Project a sat pass onto a healpix map using ephemeris data
        """)
    
    parser.add_argument('--start_date', metavar='\b', help='Date from which to start aligning data. Ex: 2019-10-10')
    parser.add_argument('--stop_date', metavar='\b', help='Date until which to align data. Ex: 2019-10-11')
    parser.add_argument('--out_dir', metavar='\b', default='./../../outputs/sat_channels/',help='Output directory. Default=./../../outputs/sat_channels/')
    parser.add_argument('--plt_dir', metavar='\b', default='./../../outputs/sat_channels/window_plots',help='Output directory. Default=./../../outputs/sat_channels/window_plots/')
    parser.add_argument('--ali_dir', metavar='\b', default='./../../outputs/align_data/',help='Output directory. Default=./../../outputs/align_data/')
    parser.add_argument('--chrono_dir', metavar='\b', default='./../../outputs/sat_ephemeris/chrono_json',help='Output directory. Default=./../../outputs/sat_ephemeris/chrono_json/')
    parser.add_argument('--noi_thresh', metavar='\b', type=int, default=3,help='Noise Threshold: Multiples of MAD. Default=3.')
    parser.add_argument('--sat_thresh', metavar='\b', type=int, default=1,help='1 σ threshold to detect sats Default=1.')
    parser.add_argument('--pow_thresh', metavar='\b', type=int, default=20,help='Power Threshold to detect sats. Default=20 dB.')
    parser.add_argument('--occ_thresh', metavar='\b', type=int, default=0.80,help='Occupation Threshold of sat in window. Default=0.80')
    parser.add_argument('--alt_thresh', metavar='\b', type=int, default=0,help='Altitude Threshold of sat in window. Default=0 degrees')
    parser.add_argument('--plots', metavar='\b', default=False,help='If True, create a gazzillion plots for each sat pass. Default = False')
    
    args = parser.parse_args()
    
    chrono_dir =        args.chrono_dir
    start_date =        args.start_date
    stop_date =         args.stop_date
    out_dir =           args.out_dir
    plt_dir =           args.plt_dir
    ali_dir =           args.ali_dir
    noi_thresh =        args.noi_thresh
    sat_thresh =        args.sat_thresh
    pow_thresh =        args.pow_thresh
    occ_thresh =        args.occ_thresh
    alt_thresh =        args.alt_thresh
    plots =             args.plots

    ref_names=['rf0XX', 'rf0YY', 'rf1XX', 'rf1YY']
    
    
    # Save logs 
    Path(f'{out_dir}/window_maps').mkdir(parents=True, exist_ok=True)
    sys.stdout = open(f'{out_dir}/logs_{start_date}_{stop_date}.txt', 'a')

    # Help traverse all 30 min obs b/w start & stop
    dates, date_time = time_tree(start_date, stop_date)
    obs_list = [[dates[d], date_time[d][dt]] for d in range(len(dates)) for dt in range(len(date_time[d]))]

#    for o in obs_list:
#        print(o)
#        window_chan_map(o)
#        break

    # Parallization magic happens here
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(window_chan_map, obs_list)

    

