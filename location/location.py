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
        spectrum = np.fft.fftshift(fft_avg / NUM_AVG)

        # Obtain frequency axis
        faxis = self.fft_f_axis(freq)

        return spectrum, faxis

    def fft_f_axis(self, freq):
        """Process the FFT to more reabale form and create frequency axis."""
        # create frequency axis, noting that Fc is in centre
        fstep = self.SAMPLE_RATE / self.NUM_SAMPLES  # fft bin size
        fstep = fstep / 1e6  # convert to MHz
        freq = freq / 1e6  # Convert to MHz

        faxis = [freq - (fstep * (self.NUM_SAMPLES / 2)) + k * fstep
                 for k in range(self.NUM_SAMPLES)]

        return faxis

    def GPIO_setup():
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


class GPSReader:
    def __init__(self):
        pass

class peakFinder:
    def __init__(self):
        pass


class LocationMeasurements(baseSDRControl):
    """Inherits baseSDRControl to provide interface for RTL SDR control.

    Process the collected FFTs in to the required data.
    """

    def __init__(self, SAMPLE_RATE, NUM_SAMPLES, GAIN):
        """Init method."""
        super().__init__(SAMPLE_RATE, NUM_SAMPLES, GAIN)

    def peak_search():
        super().fft_f_axis().faxis
        pass

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


class fftColect:
    """class to perform FFT collection from RTL-SDR."""

    # class variables
    num_avg = 100
    num_samples = 5 * 1024
    flag = False
    i = 1
    sample_rate = 2.048e6

    def __init__(self, freq_mhz):
        """Initialise instance variables."""

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
            faxis.append(
                ((sdr.center_freq / 1000000) - (fstep * (len(spectrum) / 2)))
                + k * fstep
            )
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
        np.save(
            dir
            + "/"
            + "%s-%.1fMHz-%.4fMHz-raw_samples" % (time_for_save, freq_mhz, sample_rate),
            samples,
        )

        # print confirmation of file name used to terminal
        file_name = "%s-%.1fMHz-%.4fMHz-raw_samples" % (
            time_for_save,
            freq_mhz,
            sample_rate,
        )
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

        file_name = self.raw_save(
            time_for_save, self.freq_mhz, self.sample_rate, spectrum, current_date
        )

        try:
            # Disconnect SDR
            sdr.close()

        except:
            print("\nFailed to Close RTL SDR\n")

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
            print("\nThis Device Has Recovered From a Communication Error\n")

        if flag is False:
            print("\nThis Device Has Not Recovered From a Communication Error\n")



def formated_plot(faxis, spectrum, cal_factor):

    plt.figure()

    plt.plot(faxis, (spectrum.real + cal_factor), label="Received Power")

    ymin = faxis[0]
    ymax = faxis[-1]

    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Received Power (dBm)')
    plt.title('FFT of Spectrum')
    plt.grid()
    plt.legend(loc='upper left', fontsize='small')
    plt.autoscale(enable=True, axis='x', tight=True)


if __name__ == "__main__":

    # TODO don't forget to shift tuning frequency to avoid DC leakage.

    SAMPLE_RATE = 2.048e6
    NUM_SAMPLES = 1024
    GAIN = 49

    CAL_FACTOR_71 = -135
    CAL_FACTOR_869 = -137
    FREQ_OFFSET = 0.1
    PEAK_SEARCH_RANGE = 0.05

    with LocationMeasurements(SAMPLE_RATE, NUM_SAMPLES, GAIN) as m:
        if HAS_GPIO:
            # Activate 70MHz antenna
            m.GPIO_switch(16, 1)

        # 71MHz test
        spectrum_71, faxis_71 = m.averaged_ffts(71e6)

        if HAS_GPIO:
            # Deactivate 70MHz antenna
            m.GPIO_switch(16, 0)
            # Activate 868MHz antenna
            m.GPIO_switch(18, 1)

        # 869MHz test
        spectrum_869, faxis_869 = m.averaged_ffts(869.525e6)

        if HAS_GPIO:
            # Deactivate 868MHz antenna
            m.GPIO_switch(18, 0)

    if m.con_error_flag is True:
        print("\n[i] This Device Has Recovered From a Communication Error")

    if HAS_SCREEN:
        formated_plot(faxis_71, spectrum_71, CAL_FACTOR_71)
        formated_plot(faxis_869, spectrum_869, CAL_FACTOR_869)

        plt.show()

    print("\n[\033[0:32m\u2713\033[0;0m]Complete")

    #test.sdr.close()

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
