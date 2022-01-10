"""Run a test using an RTL SDR to find the peaks in a spectrum."""
import time
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import gpsd
import peakutils
from scipy.signal import find_peaks

from rtlsdr import RtlSdr
from rtlsdr.rtlsdr import LibUSBError

# find out if the device has GPIO pins
try:
    import RPi.GPIO as gpio

    print("[\033[0:32m\u2713\033[0;0m] GPIO Pins Available on This Device")
    HAS_GPIO = True

except ImportError:
    print("[\033[31mX\033[0;0m] GPIO Pins Not Available on This Device")
    HAS_GPIO = False

# find out if device has a screen attached
try:
    plt.figure()
    plt.close()
    print("[\033[0:32m\u2713\033[0;0m] Screen Available on This Device")
    HAS_SCREEN = True

# FIXME find the exception thrown by plt.figure() and fix bare except.
except:
    print("\n[\033[0:31mX\033[0;0m] Screen Not Available on This Device")
    HAS_SCREEN = False


class baseSDRControl:
    """Base class for SDR control set up and general measurement functions.

    Set up SDR object with required parameters and conduct sampling.
    GPIO antenna switching.
    """

    """Class variables"""
    con_error_flag = False
    i = 1

    def __init__(self, SAMPLE_RATE, NUM_SAMPLES, GAIN):
        """Initialise instance variables."""
        self.SAMPLE_RATE = SAMPLE_RATE
        self.NUM_SAMPLES = NUM_SAMPLES
        self.GAIN = GAIN
        self.sdr = None
        self.spectrum = None

    def __enter__(self):
        """Enter method for context manager - set up SDR."""
        self.sdr_set_up()

        if HAS_GPIO:
            self.GPIO_setup()

        return self

    def __exit__(self, type, value, traceback):
        # FIXME add error handling details to __exit__.
        """Exit method for context manager - close SDR."""
        self.sdr.close()

        if HAS_GPIO:
            gpio.cleanup()

    def sdr_set_up(self):
        """Attempt to setup RTL-SDR with chosen perameters."""
        try:

            # Create device
            self.sdr = RtlSdr()

            # configure device
            self.sdr.sample_rate = self.SAMPLE_RATE  # Hz
            self.sdr.gain = self.GAIN

            print(f"[i] Sampling at {self.SAMPLE_RATE / 1e6} MHz\n")

            return self.sdr

        except (LibUSBError):

            print("[\033[0:31mX\033[0;0m] RTL SDR Communication Error")
            # print(sys.exc_info()[:])

            self.con_error_flag = True

            if self.i <= 60:

                time.sleep(1)
                print(
                    f"[i] Reconnection Attempt: {self.i} of 60\n"
                )
                self.i = self.i + 1
                self.sdr_set_up()

            else:

                # gpio disconnect
                try:
                    gpio.cleanup()
                except:
                    print("GPIO Not Deactivated")

                # exit programme with an error message
                sys.exit("RTL SDR Device Not Connected\n")

    def get_sdr_sample(self, freq):
        """Read a set number of samples from the RTL SDR."""
        try:
            # set frequency, with offset to avoid DC leakage
            self.sdr.center_freq = freq + 0.1e6  # Hz
            # Read in samples from the device
            samples = self.sdr.read_samples(self.NUM_SAMPLES)

        except LibUSBError:

            print("Failed to read sample/n")

        return samples

    def averaged_samples(self, freq):
        """Collect and average samples to reduce noise present."""
        NUM_AVG = 10
        sample_avg = np.zeros(self.NUM_SAMPLES)

        for i in range(NUM_AVG):

            sample = self.get_sdr_sample(freq)
            sample_avg = sample_avg + sample
            # print(x)

        return sample_avg / NUM_AVG

    def averaged_ffts(self, freq):
        """Average FFTs collected to smooth trace."""
        NUM_AVG = 10
        fft_avg = np.zeros(self.NUM_SAMPLES)

        # Create a Hamming window
        w = np.hamming(self.NUM_SAMPLES)

        print(f"\n[i] Measuring at {freq/1e6} MHz")

        for i in range(NUM_AVG):

            # Collect averaged samples
            sample_avg = self.averaged_samples(freq)

            # Window samples and take FFT
            fft = np.fft.fft(sample_avg * w)

            # Convert the FFT to dB and normalise for windowing
            fft_db = 20 * np.log10(abs(fft * 2))

            # Average the FFTs
            fft_avg = fft_avg + fft_db

            # Progress bar
            percent = int(((i+1) / NUM_AVG) * 100)
            width = int((percent) / 5)
            bar = "[" + "#" * width + " " * (20 - width) + "]"

            print("\r[i] Progress " + bar + f" {percent}%", end="", flush=True)

        # shift the fft so Fc is at the centre of the plot
        self.spectrum = np.fft.fftshift(fft_avg / NUM_AVG)

        # Obtain frequency axis
        self.faxis = self.fft_f_axis(freq)

        return self.spectrum, self.faxis

    def fft_f_axis(self, freq):
        """Process the FFT to more reabale form and create frequency axis."""
        # create frequency axis, noting that Fc is in centre
        fstep = self.SAMPLE_RATE / self.NUM_SAMPLES  # fft bin size
        fstep = fstep / 1e6  # convert to MHz
        freq = freq / 1e6  # Convert to MHz

        self.faxis = [freq - (fstep * (self.NUM_SAMPLES / 2)) + k * fstep
                      for k in range(self.NUM_SAMPLES)]

        return self.faxis

    def GPIO_setup(self):
        """Set up Rpi gpio for antenna switching."""
        chan_list = [16, 18, 22, 24, 26]  # pins to be used

        # pin numbering mode
        gpio.setmode(gpio.BOARD)

        # set pins as outputs with an initial value of low
        gpio.setup(chan_list, gpio.OUT, initial=gpio.LOW)

    def GPIO_switch(self, chan, state):
        """Switch antenna."""
        # activate selected gpio
        gpio.output(chan, state)
        # wait for switch
        time.sleep(0.1)


class peakFinder:
    """Finds peaks and noise within the measured spectrum."""

    def __init__(self):
        """Is Constructor."""

    @staticmethod
    def get_peak_indexes(spectrum, faxis):
        """Find peaks in the data using a peak detector."""
        # indexes = peakutils.peak.indexes(self.spectrum.real,
        #                                  thres=0.2, min_dist=50)
        indexes, _ = find_peaks(spectrum, distance=50, prominence=10)

        # Make an array of peak amplitudes and corresponding
        # frequencies from detected peak indexes

        peaks_mag = [spectrum[indexes[i]] for i in range(len(indexes))]
        peaks_freq = [faxis[indexes[i]] for i in range(len(indexes))]

        return peaks_freq, peaks_mag

    def peak_sort(self, freq, faxis, spectrum):
        """
        Sort the peaks in to a useful order.

        Based on the distance from the measured frequency.
        """
        freq = freq/1e6

        peaks_freq, peaks_mag = self.get_peak_indexes(spectrum, faxis)

        # search for peak at frequency closest to frequency of interest
        # subtract frequency of interest from frequencies peaks are detected at
        search = [i - freq for i in peaks_freq]

        # convert values to absolute
        abs_search = np.abs(search)

        # lowest number will be closest to frequency of interest
        # find the index of this number in the list
        min_index = np.argmin(abs_search)

        # create empty lists for sorted values
        peaks_freq_sorted = []
        peaks_mag_sorted = []

        # check peak is close enough to the frequency of interest
        if (freq-0.05) < peaks_freq[min_index] < (freq+0.05):

            peaks_mag_sorted.append(peaks_mag.pop(min_index))
            peaks_freq_sorted.append(peaks_freq.pop(min_index))

        # if peak detected isn't close enough use bin at frequecny
        # of interest regardless if a peak was detected there or not
        else:

            # search for bins closest to frequency of interest and save
            search_freq = [i - freq for i in faxis]
            # convert values to absolute
            abs_search_freq = np.abs(search_freq)

            # lowest number will be closest to frequency of interest
            # find the index of this number in the list
            min_index_freq = np.argmin(abs_search_freq)

            peaks_mag_sorted.append(spectrum[min_index_freq])
            peaks_freq_sorted.append(faxis[min_index_freq])

        # order detected peaks from large to small
        peaks_index = np.argsort(peaks_mag)[::-1]

        # use peak index to retrieve data from data sets,
        # retrieve 3 highest magnitude peaks

        for i in peaks_index[:3]:

            peaks_mag_sorted.append(peaks_mag[i])
            peaks_freq_sorted.append(peaks_freq[i])

        return peaks_mag_sorted, peaks_freq_sorted

    @staticmethod
    def get_noise(spectrum, peaks):
        """Get the average of all the FFT bins.

        Excluding those where peaks were detected to aproximate noise
        """
        total_all_spectrum = np.sum(spectrum)
        total_all_peaks = np.sum(peaks)

        total_excl_peaks = total_all_spectrum - total_all_peaks

        bin_avg = total_excl_peaks / (len(spectrum)-len(peaks))

        return bin_avg


class locationMeasurements(baseSDRControl, peakFinder):
    """Inherits baseSDRControl to provide interface for RTL SDR control.

    Process the collected FFTs in to the required data.
    """

    def __init__(self, SAMPLE_RATE, NUM_SAMPLES, GAIN):
        """Init method."""
        super(locationMeasurements, self).__init__(SAMPLE_RATE, NUM_SAMPLES, GAIN)
        super(baseSDRControl, self).__init__()

    def __enter__(self):
        """Enter method for context manager - set up SDR."""
        super(locationMeasurements, self).__enter__()

        try:
            gpsd.connect()

        except:
            print("[\033[31mX\033[0;0m] GPS Not Available on This Device")

        return self

    # TODO add gps to class
    # TODO add method to execute complete test

    def gps_loc():
        pass

    def write_csv():
        pass


class DataSave:

    # Function to save the unprocessed sampled data for possible later use
    @staticmethod
    def file_name(SAMPLE_RATE, freq):
        # convert sample rate to MHz
        sample_rate_mhz = SAMPLE_RATE / 1000000
        freq_mhz = freq / 1000000
        time_for_save = time.strftime("%m_%d_%y-%H_%M_%S")
        current_date = time.strftime("%d.%m.%y")

        dir = "Test " + current_date

        if not os.path.isdir(dir):
            print("Creating New Folder\n")
            os.mkdir(dir)

        # print confirmation of file name used to terminal
        file_name = dir + "/%s-%.1fMHz-%.4fMHz-raw_samples" % (
            time_for_save,
            freq_mhz,
            sample_rate_mhz,
        )

        return file_name

    @classmethod
    def save_fft(cls, SAMPLE_RATE, freq, data):

        file_name = cls.file_name(SAMPLE_RATE, freq)
        np.save(file_name, data)

        print(file_name + " File Saved Locally\n")

    def write_csv():
        pass

    def write_sql():
        pass


class GPIOControl:
    """Set up and control of raspberry pi GPIO switching."""

    # class variables
    chan_list = [16, 18, 22, 24, 26]  # pins to be used

    def __init__(self):
        """Set up Rpi gpio for antenna switching."""
        try:
            # pin numbering mode
            gpio.setmode(gpio.BOARD)

            # set pins as outputs with an initial value of low
            gpio.setup(self.chan_list, gpio.OUT, initial=gpio.LOW)

        except NameError:
            print("GPIO Not Setup")

        return

    def switch(self, chan, state):
        """Change the state of a pin (high or low) to switch antenna."""
        try:

            # activate selected gpio
            gpio.output(chan, state)

            # wait for switch
            time.sleep(0.1)

        except NameError:
            print("GPIO Not Switched")

        return


def formated_plot(faxis, spectrum, cal_factor, freq, peak, noise):
    """Produce a formated plot of date collected in one measurement cycle."""
    plt.figure()

    peak = np.asanyarray(peak)

    ymin = faxis[0]
    ymax = faxis[-1]

    # adjust all measurements for calibration factor
    spectrum = spectrum + cal_factor
    peak = peak + cal_factor
    noise = noise + cal_factor

    plt.plot(faxis, spectrum, label="Received Power")
    plt.plot(freq, peak, 'go', label='Detected Peaks')

    # annotate plot with highest peak
    plt.annotate(f'Observed Peak\n {peak[0]:.1f} dBm \n {freq[0]:.3f} MHz',
                 xy=(freq[0], peak[0]), xycoords='data',
                 xytext=(0.65, 0.75), textcoords='figure fraction',
                 arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3,rad=.2"))

    # plot noise level
    plt.plot([ymin, ymax], [noise, noise], 'r--',
             label="Estimated Noise Level")

    # annotate plot with noise plt
    plt.annotate(f'Estimated Noise  \n {noise:.1f} dBm',
                 xy=(faxis[int(len(faxis)/2)], noise),
                 xycoords='data', xytext=(0.2, 0.6),
                 textcoords='figure fraction')

    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Received Power (dBm)')
    plt.title('FFT of Spectrum')
    plt.grid()
    plt.legend(loc='upper left', fontsize='small')
    plt.autoscale(enable=True, axis='x', tight=True)


if __name__ == "__main__":

    # TODO don't forget to shift tuning frequency to avoid DC leakage.

    SAMPLE_RATE = 2.048e6
    NUM_SAMPLES = 1024 * 5
    GAIN = 49

    CAL_FACTOR_71 = -135
    CAL_FACTOR_869 = -137
    FREQ_OFFSET = 0.1
    PEAK_SEARCH_RANGE = 0.05

    with locationMeasurements(SAMPLE_RATE, NUM_SAMPLES, GAIN) as m:
        if HAS_GPIO:
            # Activate 70MHz antenna
            m.GPIO_switch(16, 1)

        # 71MHz test
        spectrum_71, faxis_71 = m.averaged_ffts(71e6)
        # freq_71, peaks_71 = m.get_peak_indexes()
        peak_71, freq_71 = m.peak_sort(71e6, faxis_71, spectrum_71)

        bin_avg_71 = m.get_noise(spectrum_71, peak_71)

        if HAS_GPIO:
            # Deactivate 70MHz antenna
            m.GPIO_switch(16, 0)
            # Activate 868MHz antenna
            m.GPIO_switch(18, 1)

        # 869MHz test
        spectrum_869, faxis_869 = m.averaged_ffts(869.525e6)
        # freq_869, peaks_869 = m.get_peak_indexes()
        peak_869, freq_869 = m.peak_sort(869.525e6, faxis_869, spectrum_869)

        bin_avg_869 = m.get_noise(spectrum_869, peak_869)

        if HAS_GPIO:
            # Deactivate 868MHz antenna
            m.GPIO_switch(18, 0)

    if m.con_error_flag is True:
        print("\n[i] This Device Has Recovered From a Communication Error")

    if HAS_SCREEN:
        formated_plot(faxis_71, spectrum_71, CAL_FACTOR_71, freq_71, peak_71,
                      bin_avg_71)
        formated_plot(faxis_869, spectrum_869, CAL_FACTOR_869, freq_869, peak_869,
                      bin_avg_869)

        plt.show()

    print("\n[\033[0:32m\u2713\033[0;0m]Complete")

    # test.sdr.close()

    # test.sdr_set_up(1, False, 2.048e6)
    # Set up never ending loop

    # test_71 = fftColect(71)
    # test_869 = fftColect(869.525)

    # while True:
    #     try:
    #         # test_71.perform()
    #         # test_869.perform()

    # # wait X seconds before next loop
    # time.sleep(5)

    #       except KeyboardInterrupt:

    #          sys.exit("\nStopped by the user\n")
