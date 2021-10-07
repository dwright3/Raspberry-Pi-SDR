"""Run a test useing an RTL SDR to find the peaks in a spectrum."""
import time
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

from rtlsdr import RtlSdr
from rtlsdr.rtlsdr import LibUSBError

# find out if the device has GPIO pins
try:
    import RPi.GPIO as gpio
    HAS_GPIO = True

except ImportError:
    print("GPIO Pins Not Available on This Device")
    HAS_GPIO = False

# find out if device has a screen attached
try:
    plt.figure()
    HAS_SCREEN = True

# FIXME find the exection thrown by plt.figure() and fix bare except.
except:
    HAS_SCREEN = False


class SDRControl:
    """Set up SDR object with required parameters and conduct sampling."""

    """Class variables"""
    con_error_flag = False
    i = 1

    def __init__(self):
        """Initialise instance variables."""
        self.SAMPLE_RATE = SAMPLE_RATE
        self.NUM_SAMPLES = NUM_SAMPLES
        self.GAIN = GAIN
        self.sdr_set_up(self.i, self.con_error_flag, self.GAIN)

    def sdr_set_up(self, i, flag, GAIN):
        """Attempt to setup RTL-SDR with chosen perameters."""
        try:

            # Create device
            self.sdr = RtlSdr()

            # configure device
            self.sdr.sample_rate = self.SAMPLE_RATE  # Hz
            self.sdr.gain = GAIN

            print("Sampling at %.3f MHz\n" % (self.SAMPLE_RATE/1e6))

            return self.sdr

        except (LibUSBError):

            print("RTL SDR Communication Error")
            # print(sys.exc_info()[:])

            flag = True

            if i <= 60:

                time.sleep(1)
                print("Attempting to Re-establish Connection...... Attempt: %d of 60\n" % i)
                i = i + 1
                self.sdr_set_up(i, flag, GAIN)

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


class DataCollection(SDRControl):
    """Inherits SDRControl to provide interface for RTL SDR control."""

    """ provides data collection methods."""

    def __init__(self, SAMPLE_RATE, NUM_SAMPLES, GAIN):
        """Init method with call to super class init method."""
        # self.SAMPLE_RATE = SAMPLE_RATE
        # self.NUM_SAMPLES = NUM_SAMPLES
        # self.GAIN = GAIN
        super().__init__() #self.SAMPLE_RATE, self.NUM_SAMPLES, self.GAIN)

    def averaged_samples(self, freq):
        """Collect and average samples to reduce noise present."""
        NUM_AVG = 10
        sample_avg = np.zeros(self.NUM_SAMPLES)
        x = 1

        while x <= NUM_AVG:

            sample = super().get_sdr_sample(freq)
            sample_avg = sample_avg + sample
            # print(x)
            x += 1

        return sample_avg/NUM_AVG

    def averaged_ffts(self, freq):
        """Average FFTs collected tp smooth trace."""
        NUM_AVG = 10
        fft_avg = np.zeros(self.NUM_SAMPLES)
        x = 1

        while x <= NUM_AVG:

            sample_avg = self.averaged_samples(freq)

            w = np.hamming(self.NUM_SAMPLES)
            # Process fft
            # take fft of samples
            fft = np.fft.fft(sample_avg * w)

            # convert to dB
            fft_db = 20 * np.log10(abs(fft * 2))

            fft_avg = fft_avg + fft_db
            print(x)
            x += 1

        return fft_avg/NUM_AVG


class DataProcessor:
    """Process the collected FFTs in to the required data."""

    def __init__(self, SAMPLE_RATE, NUM_SAMPLES):
        """Init method method."""
        self.SAMPLE_RATE = SAMPLE_RATE
        self.NUM_SAMPLES = NUM_SAMPLES

    def processed_fft(self, freq, data):
        """Process the FFT to more reabale form and create frequency axis."""
        # shift the fft so Fc is at the centre of the plot
        spectrum = np.fft.fftshift(data)

        # create frequency axis, noting that Fc is in centre
        fstep = self.SAMPLE_RATE / self.NUM_SAMPLES  # fft bin size
        fstep = fstep / 1000000  # convert to MHz

        faxis = []
        k = 0
        while k < self.NUM_SAMPLES:
            # create f axis with Fc in the centre
            faxis.append(((freq / 1000000) - (fstep * (self.NUM_SAMPLES / 2))) + k * fstep)
            k += 1

        return spectrum, faxis

    def peak_search():
        pass

    def process_and_peak_together():
        pass


class DataSave:

    def __init__(self, SAMPLE_RATE, freq):
        self.SAMPLE_RATE = SAMPLE_RATE
        self.freq = freq

    # Function to save the unprocessed sampled data for possible later use
    def file_name(self):
        # convert sample rate to MHz
        sample_rate_mhz = self.SAMPLE_RATE / 1000000
        freq_mhz = self.freq / 1000000
        time_for_save = time.strftime("%m_%d_%y-%H_%M_%S")
        current_date = time.strftime("%d.%m.%y")

        dir = "Test " + current_date

        if not os.path.isdir(dir):
            print("Creating New Folder\n")
            os.mkdir(dir)

        # print confirmation of file name used to terminal
        file_name = '%s-%.1fMHz-%.4fMHz-raw_samples' % (time_for_save, freq_mhz, sample_rate_mhz)

        return file_name

    def save_fft(self, file_name):

        np.save(file_name, self.data)

        print(file_name + " File Saved Locally\n")

    def write_csv():
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



class DisplayResults:
    """Class to plot collected data."""

    # class variables
    cal_factor_71 = -135
    cal_factor_869 = -137
    freq_offset = 0.1
    peak_search_range = 0.05

    def __init__(self, data, peaks_list, freq, faxis):
        """Initialise instance variables."""
        self.plot_object = plt.figure()
        self.data = data
        self.peaks_list = peaks_list
        self.freq = freq
        self.faxis = faxis

    def plot_data(self, cal_factor_71):

        # plot the FFT
        plt.plot(self.faxis, (self.data.real+cal_factor_71), label='Received Power')

        ymin = self.faxis[0]
        ymax = self.faxis[-1]

    def annotate_data(self):
        pass

    def format_plot(self):
        pass

    def main(self):
        pass


class fftColect:
    """class to perform FFT collection from RTL-SDR."""

    # class variables
    num_avg = 100
    num_samples = 5*1024
    flag = False
    i = 1
    sample_rate = 2.048e6

    def __init__(self, freq_mhz):
        """Initialise instance variables"""

        self.freq_mhz = freq_mhz
        self.freq = freq_mhz * 1e6

    def sdr_control(self, freq, i, flag, sample_rate):

        try:

            # Create device
            sdr = RtlSdr()

            # configure device
            sdr.sample_rate = sample_rate  # Hz
            sdr.center_freq = freq + 0.1e6  # Hz
            sdr.gain = 49

            print("Sampling at %.2f MHz\n" % (self.freq_mhz))

            return sdr, flag

        except:

            print("RTL SDR Communication Error")
            print(sys.exc_info()[:])

            flag = True

            if i <= 60:

                time.sleep(1)
                print("Attempting to Re-establish Connection...... Attempt: %d\n" % i)
                i = i + 1
                sdr, flag = self.sdr_control(freq, i, flag)

            else:

                # gpio disconnect
                try:
                    gpio.cleanup()
                except:
                    print("GPIO Not Deactivated")

                # exit programme with an error message
                sys.exit("RTL SDR Device Not Connected\n")

        return sdr, flag

    def fft(self, sdr, num_samples):
        try:
            # Read in samples from the device
            samples = sdr.read_samples(num_samples)

            w = np.hamming(num_samples)
            # Process fft
            # take fft of samples
            fft = np.fft.fft(samples * w)

            # convert to dB
            spectrum = 20 * np.log10(abs(fft * 2))

            # print("FFT Ready..... \n")

        except:
            spectrum = 0
            print("FFT Failed \n")

        return spectrum


    # Function to get samples and create FFT
    def data(self, sdr, num_avg, num_samples):
        print("Data Capture in Progress........\n")

        x = 1
        a = 1

        spectrum_avg = np.zeros(num_samples)

        while x <= num_avg:
            # time.sleep(0.1)
            spectrumA = self.fft(sdr, num_samples)
            spectrum_avg = spectrum_avg + spectrumA
            if a == 100:
                percent_comp = (x / num_avg) * 100
                print("%d Averages Taken" % x)
                print("Sampling %.2f %% Complete\n" % percent_comp)

                a = 1
            else:
                a += 1
            x += 1

        spectrum = spectrum_avg / num_avg

        print("Data Capture Complete\n")

        # shift the fft so Fc is at the centre of the plot
        spectrum = np.fft.fftshift(spectrum)

        array_length = len(spectrum)

        # create frequency axis, noting that Fc is in centre
        fstep = sdr.sample_rate / len(spectrum)  # fft bin size
        fstep = fstep / 1000000  # convert to MHz

        faxis = []
        k = 0
        while k < array_length:
            # create f axis with Fc in the centre
            faxis.append(((sdr.center_freq / 1000000) - (fstep * (len(spectrum) / 2))) + k * fstep)
            # below creates f axis with Fc at the start
            # faxis.append((sdr.center_freq/1000000) + k * fstep)
            k = k + 1

        return spectrum, faxis

    # Function to set up Rpi gpio for antenna switching
    def gpio_set(self):
        try:
            # pin numbering mode
            gpio.setmode(gpio.BOARD)

            # pins to be used
            chan_list = [16, 18, 22, 24, 26]

            # set pins as outputs with an initial value of low
            gpio.setup(chan_list, gpio.OUT, initial=gpio.LOW)

        except NameError:
            print("GPIO Not Setup")

        return

    # function to switch antenna
    def gpio_switch(self, chan, state):
        try:

            # activate selected gpio
            gpio.output(chan, state)

            # wait for switch
            time.sleep(0.1)

        except NameError:
            print("GPIO Not Switched")

        return

    # Function to produce strings with time and date
    def time_date(self):
        # string including date and time
        current_time = time.strftime("%d/%m/%y %H:%M:%S")
        # string with just date
        current_date = time.strftime("%d.%m.%y")
        # string with just time
        current_hour = time.strftime("%H:%M:%S")
        # string with date and time in a format suitable for use as a file name
        time_for_save = time.strftime("%m_%d_%y-%H_%M_%S")

        return current_date, current_hour, current_time, time_for_save

        # Function to save the unprocessed sampled data for possible later use
    def raw_save(self, time_for_save, freq_mhz, sample_rate, samples, current_date):
        # convert sample rate to MHz
        sample_rate = sample_rate / 1000000

        dir = "Test " + current_date

        if not os.path.isdir(dir):
            print("Creating New Folder\n")
            os.mkdir(dir)

        # save samples to .NPY file
        np.save(dir + "/" + '%s-%.1fMHz-%.4fMHz-raw_samples' % (time_for_save, freq_mhz, sample_rate), samples)

        # print confirmation of file name used to terminal
        file_name = '%s-%.1fMHz-%.4fMHz-raw_samples' % (time_for_save, freq_mhz, sample_rate)
        print(file_name + " File Saved Locally\n")

        return file_name

    def perform(self):

        # Set up GPIO
        self.gpio_set()

        # Activate correct antenna
        if self.freq < 500e6:
            # Activate 70MHz antenna
            self.gpio_switch(16, 1)

        elif self.freq >= 500e6:
            # Activate 868MHz antenna
            self.gpio_switch(18, 1)

        else:
            print("Antenna Switch Failure \n")

        # Set up SDR
        sdr, flag = self.sdr_control(self.freq, self.i, self.flag, self.sample_rate)

        print(flag)

        # Collect data
        spectrum, faxis = self.data(sdr, self.num_avg, self.num_samples)

        current_date, current_hour, current_time, time_for_save = self.time_date()

        file_name = self.raw_save(time_for_save, self.freq_mhz,
                                  self.sample_rate, spectrum, current_date)

        try:
            # Disconnect SDR
            sdr.close()

        except:
            print('\nFailed to Close RTL SDR\n')

        # Deactivate correct antenna
        if self.freq < 500e6:
            # Deactivate 70MHz antenna
            self.gpio_switch(16, 0)

        elif self.freq >= 500e6:
            # Deactivate 868MHz antenna
            self.gpio_switch(18, 0)

        else:
            print("Antenna Switch Failure \n")

        # GPIO disconnect
        try:
            gpio.cleanup()

        except NameError:
            print("GPIO Not Deactivated")

        # flag = True

        if flag is True:
            print('\nThis Device Has Recovered From a Communication Error\n')

        if flag is False:
            print('\nThis Device Has Not Recovered From a Communication Error\n')


if __name__ == '__main__':

    # TODO don't forget to shift tuning frequency to avoid DC leakage.

    SAMPLE_RATE = 2.048e6
    NUM_SAMPLES = 1024
    GAIN = 49


    # test = SDRControl(2.048e6)

    # collect = DataCollection(test)

    # data = collect.averaged_ffts()

    test = DataCollection(SAMPLE_RATE, NUM_SAMPLES, GAIN)

    # fft = test.averaged_ffts(71e6)

    # w = np.hamming(num_samples)
    # Process fft
    # take fft of samples
    # fft = np.fft.fft(data)

    # # convert to dB
    # spectrum = 20 * np.log10(abs(fft * 2))

    data = test.averaged_ffts(71e6)

    processor = DataProcessor(SAMPLE_RATE, NUM_SAMPLES)

    specrum, faxis = processor.processed_fft(71e6, data)

    plt.Figure()

    plt.plot(faxis, spectrum)

    plt.show()

    test.sdr.close()

    #test.sdr_set_up(1, False, 2.048e6)
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
