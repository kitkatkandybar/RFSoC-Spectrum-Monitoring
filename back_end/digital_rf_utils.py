"""
This file is a modified version of drf_plot.py from the DigitalRF library, which reads in Digital RF data and processes it
for graphing purposes
"""

import traceback
import sys
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import digital_rf



def spectrum_process(
    data,
    sfreq,
    cfreq,
    toffset,
    modulus,
    integration,
    bins,
    log_scale,
    zscale,
    detrend,
    title,
    clr,
):
    """
    Process data into a form useable for spectrum and spectrogram graphs.

    Break spectrum by modulus and display each block. Integration here acts
    as a pure average on the spectral data.
    """

    if detrend:
        dfn = matplotlib.mlab.detrend_mean
    else:
        dfn = matplotlib.mlab.detrend_none

    win = np.blackman(bins)

    if modulus:
        block = 0
        block_size = integration * modulus
        block_toffset = toffset
        while block < len(data) / block_size:

            vblock = data[block * block_size : block * block_size + modulus]
            pblock, freq = matplotlib.mlab.psd(
                vblock,
                NFFT=bins,
                Fs=sfreq,
                detrend=dfn,
                window=win,
                scale_by_freq=False,
            )

            # complete integration
            for idx in range(1, integration):

                vblock = data[
                    block * block_size
                    + idx * modulus : block * block_size
                    + idx * modulus
                    + modulus
                ]
                pblock_n, freq = matplotlib.mlab.psd(
                    vblock,
                    NFFT=bins,
                    Fs=sfreq,
                    detrend=dfn,
                    window=matplotlib.mlab.window_hanning,
                    scale_by_freq=False,
                )
                pblock += pblock_n

            pblock /= integration


            yield pblock, freq

            block += 1
            block_toffset += block_size / sfreq

    else:
        pdata, freq = matplotlib.mlab.psd(
            data, NFFT=bins, Fs=sfreq, detrend=dfn, window=win, scale_by_freq=False
        )
  

        yield pdata, freq



def get_drf_channels(input_file):
    try:
        drf = digital_rf.DigitalRFReader(input_file)
        chans = drf.get_channels()
        return chans
    except:
        print(("problem loading file %s" % f))
        traceback.print_exc(file=sys.stdout)
        raise

def get_n_samples(input_file, channel):
    try:
        drf = digital_rf.DigitalRFReader(input_file)
        ustart, ustop = drf.get_bounds(channel)
        n_total_samples = ustop - ustart
        return n_total_samples
    except:
        print(("problem loading file %s" % f))
        traceback.print_exc(file=sys.stdout)
        raise

def read_digital_rf_data(input_files, plot_file=None, plot_type="spectrum", channel="",
		subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=0, modulus=None, integration=1, 
		zscale=(0, 0), bins=256, log_scale=False, detrend=False,msl_code_length=0,
        msl_baud_length=0,save_plot = False, title="title"):

    for f in input_files:
        # read in options and convert to variables
        try:
            drf = digital_rf.DigitalRFReader(f)



            chans = drf.get_channels()
            if channel == "":
                chidx = 0
            else:
                chidx = chans.index(channel)

            ustart, ustop = drf.get_bounds(chans[chidx])
            n_total_samples = ustop - ustart

            drf_properties = drf.get_properties( chans[chidx])
            sfreq_ld       = drf_properties["samples_per_second"]
            sfreq          = float(sfreq_ld)
            toffset        = start_sample

            if atime == 0:
                atime = ustart
            else:
                atime = int(np.uint64(atime * sfreq_ld))

            sstart = atime + int(toffset)
            dlen   = stop_sample - start_sample

            req_start_time = digital_rf.util.sample_to_datetime(sstart, sfreq).timestamp()
            req_end_time   = digital_rf.util.sample_to_datetime(sstart + dlen, sfreq).timestamp()

            metadata_samples = None
            if cfreq is None:
                # read center frequency from metadata
                metadata_samples = drf.read_metadata(
                    start_sample=sstart,
                    end_sample=sstart + dlen,
                    channel_name=chans[chidx],
                )
                # use center frequency of start of data, even if it changes
                for metadata in metadata_samples.values():
                    try:
                        cfreq = metadata["center_frequencies"].ravel()[subchan]
                    except KeyError:
                        continue
                    else:
                        break
                if cfreq is None:
                    print(
                        "Center frequency metadata does not exist for given"
                        " start sample."
                    )
                    cfreq = 0.0

            d = drf.read_vector(sstart, dlen, chans[chidx], subchan)

            if len(d) < (stop_sample - start_sample):
                print(
                    "Probable end of file, the data size is less than expected value."
                )
                sys.exit()

            if msl_code_length > 0:
                d = apply_msl_filter(d, msl_code_length, msl_baud_length)



        except:
            print(("problem loading file %s" % f))
            traceback.print_exc(file=sys.stdout)
            raise
            # sys.exit()


    # 'spectrum' plot type also works for spectrogram data 
    if plot_type == "spectrum":
        data = { 
            'metadata': {
                'cfreq': cfreq, 'sfreq': sfreq, 'channel': chans[chidx],
                'start_time': req_start_time, 'end_time': req_end_time,
            },
            'data': [],
        }
        if metadata_samples:
            data['metadata']['metadata_samples'] = metadata_samples.popitem()[1]
        gen = spectrum_process(
            d,
            sfreq,
            cfreq,
            toffset,
            modulus,
            integration,
            bins,
            log_scale,
            zscale,
            detrend,
            title,
            "b",
        )
        for g in gen:
            data['data'].append({'data': g[0], 'freq': g[1]})
        return data

if __name__ == "__main__":
    # default values
    input_files     = []
    sfreq           = 0.0
    cfreq           = None
    plot_type       = None
    channel         = ""
    subchan         = 0  # sub channel to plot
    atime           = 0
    start_sample    = 0
    stop_sample     = 0
    modulus         = None
    integration     = 1

    zscale          = (0, 0)

    bins            = 256

    title           = ""
    log_scale       = False
    detrend         = False
    show_plots      = True
    plot_file       = ""

    msl_code_length = 0
    msl_baud_length = 0


    # imitate command
    # drf_plot.py -i "C:/Users/yanag/openradar/openradar_antennas_wb_hf/" -c discone:0 -r 0:1000000 -p specgram -b 1024 -l
    read_digital_rf_data(["C:/Users/yanag/openradar/openradar_antennas_wb_hf/"], plot_file=None, plot_type="spectrum", channel="discone",
		subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=None, integration=1, 
		zscale=(0, 0), bins=1023, log_scale=True, detrend=False,msl_code_length=0,
        msl_baud_length=0)