## Imports ##
from rtlsdr import RtlSdr
import numpy
import matplotlib.pyplot as plt
import time
import peakutils
import csv
import sys

try:
    import RPi.GPIO as gpio
    
except:
    print("\nGPIO Pins Not Available on This Device\n")
 
 
## Function Definitions ##

# Function to produce strings with time and date
def time_date():
    # string including date and time
    current_time = time.strftime("%d/%m/%y %H:%M:%S")
    # string with just date
    current_date = time.strftime("%d/%m/%y")
    # string with just time
    current_hour = time.strftime("%H:%M:%S")
    # string with date and time in a format suitable for use as a file name
    time_for_save = time.strftime("%m_%d_%y-%H_%M_%S")
    
    return current_date, current_hour, current_time, time_for_save

# Function to detect peaks in the data
def peak_det(spectrum, faxis):
    # Find peaks in the data using a peak detector (good for more that 1 peak, min_dist needs work)
    indexes = peakutils.peak.indexes(spectrum.real,thres=0.1, min_dist=250)
    
    # Make an array of peak amplitudes and corresponding frequencies from detected peak indexes
    x = 0
    peaks = []
    freq = []
    while x < len(indexes):
        peaks.append(spectrum.real[indexes[x]])
        freq.append(faxis[indexes[x]])
        x += 1

    # order detected peaks from small to large
    peaks_index = numpy.argsort(peaks)
    
    # use peak index to retrieve data from data sets
    amp_peak_1 = peaks[peaks_index[len(peaks_index)-1]]
    freq_peak_1 = freq[peaks_index[len(peaks_index)-1]]
    amp_peak_2 = peaks[peaks_index[len(peaks_index)-2]]
    freq_peak_2 = freq[peaks_index[len(peaks_index)-2]]
    amp_peak_3 = peaks[peaks_index[len(peaks_index)-3]]
    freq_peak_3 = freq[peaks_index[len(peaks_index)-3]]
    amp_peak_4 = peaks[peaks_index[len(peaks_index)-4]]
    freq_peak_4 = freq[peaks_index[len(peaks_index)-4]]
    amp_peak_5 = peaks[peaks_index[len(peaks_index)-5]]
    freq_peak_5 = freq[peaks_index[len(peaks_index)-5]]
    
    return amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, indexes

# Function to display results and write to a .CSV and .TXT file
def display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5):
    # print first 2 detected peaks
    print('%s %s Peaks: %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz and %.2f dB at %.3f MHz\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5))

    # write peaks to a text file
    with open("log.txt","a") as f:
        f.write('%s %s Peaks: %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz and %.2f dB at %.3f MHz\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5))
        
    f.close()

    #write peaks to a .CSV file
    with open('log.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
        writer.writerow([current_date] + [current_hour] + [amp_peak_1] + [freq_peak_1] + [amp_peak_2] + [freq_peak_2] + [amp_peak_3] + [freq_peak_3] + [amp_peak_4] + [freq_peak_4] + [amp_peak_5] + [freq_peak_5])

    csvfile.close()

    return

# Function to get samples and create FFT
def data(sdr):
    # Read in samples from the device
    samples = sdr.read_samples(5000)
              
    # Process fft
    # take fft of samples
    fft = numpy.fft.fft(samples)
    # shift the fft so Fc is at the centre of the plot
    fft_shift = numpy.fft.fftshift(fft)
    # convert to dB
    spectrum = 20 * numpy.log10(abs(fft_shift)) 
    
    # below creates fft without shift to centre
    # spectrum = 20 * numpy.log10(abs(numpy.fft.fft(samples)))
    
    print ("FFT Ready\n")
                    
    array_length = len(samples)
        
    # create frequency axis, noting that Fc is in centre
    fstep = sdr.sample_rate/len(spectrum) # fft bin size
    fstep = fstep / 1000000 #  convert to MHz
        
    faxis = []
    k = 0
    while k < array_length:
        # create f axis with Fc in the centre
        faxis.append(((sdr.center_freq/1000000)-(fstep*(len(spectrum)/2))) + k * fstep)
        # below creates f axis with Fc at the start
        # faxis.append((sdr.center_freq/1000000) + k * fstep)
        k = k + 1


    return spectrum, faxis, samples

# Function to set up and configure SDR
def sdr_control(freq):

    try:
        # Create device
        sdr = RtlSdr()

        # configure device
        sdr.sample_rate = 2.048e6  # Hz
        sdr.center_freq = freq   # Hz
        sdr.gain = 49
    
    except:
        # gpio disconnect
        try:
            gpio.cleanup()
        except:
            print("GPIO Not Deactivated")
        # exit programme with an error message
        sys.exit("RTL SDR Device Not Connected\n")
        
    return sdr

# Function to set up Rpi gpio for antenna switching
def gpio_set():
    
    try:
        # pin numbering mode
        gpio.setmode(gpio.BOARD)

        # pins to be used
        chan_list = [16,18,22,24,26]

        # set pins as outputs with an initial value of low
        gpio.setup(chan_list, gpio.OUT, initial=gpio.LOW)
    
    except:
        print("GPIO Not Setup")

    return

# function to switch antenna
def gpio_switch(chan, state):
    
    try:

        # activate selected gpio
        gpio.output(chan, state)

        # wait for switch
        time.sleep(0.5)
    
    except:
        print("GPIO Not Switched")
    
    return

# Function to plot the FFT's to aid debugging
def debug_graph(faxis,spectrum,indexes,faxis2,spectrum2,indexes2):
    
    try:
        # plot the data from the 70MHz sample period
        plt.plot(faxis,spectrum.real)

        # Plot all detected peaks
        x = 0
        while x < len(indexes):
            plt.plot(faxis[indexes[x]], spectrum.real[indexes[x]], 'ro')
            x += 1

        # format plot
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Relative Power (dB)')
        plt.title('FFT of Spectrum')
        plt.grid()

        plt.figure()
        # plot the data from the last sample period
        plt.plot(faxis2,spectrum2.real)

        # Plot all detected peaks
        x = 0
        while x < len(indexes2):
            plt.plot(faxis2[indexes2[x]], spectrum2.real[indexes2[x]], 'ro')
            x += 1

        # format plot
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Relative Power (dB)')
        plt.title('FFT of Spectrum')
        plt.grid()
        plt.show()
        
    except:
        
        print("\nComplete\n")
    
    return

# Function to save the unprocessed sampled data for possible later use
def raw_save(time_for_save,freq_mhz,sample_rate,samples):
    
    # convert sample rate to MHz
    sample_rate = sample_rate/1000000
    
    # save samples to .NPY file
    numpy.save('%s-%.1fMHz-%.4fMHz-raw_samples' % (time_for_save,freq_mhz,sample_rate) , samples)
    
    # print confirmation of file name used to terminal
    print ('%s-%.1fMHz-%.4fMHz-raw_samples file saved \n' % (time_for_save,freq_mhz,sample_rate))
    
    return 


## Main Body ##

# set up gpio
gpio_set()

# Set first frequency of interest and display in MHz
freq = 71e6
freq_mhz = freq/1000000
print("Sampling at %.2f MHz\n" % freq_mhz)

# Activate 70MHz antenna
gpio_switch(18,1)

# Set up SDR
sdr = sdr_control(freq)

# Collect Data  
spectrum, faxis, samples = data(sdr)

# Detect Peaks   
amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, indexes = peak_det(spectrum, faxis)

# Get current time and date    
current_date, current_hour, current_time, time_for_save = time_date()

# Save the sampled data for later use if needed 
raw_save(time_for_save,freq_mhz,sdr.sample_rate, samples)

# Record results
display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5)

# Disconnect SDR
sdr.close()

# Deactivate 70MHz antenna
gpio_switch(18,0)
    
# Taking second sample

# Set second frequency of interest and display in MHz
freq = 869e6
freq_mhz = freq/1000000
print("Sampling at %.2f MHz\n" % freq_mhz)

# Activate 868MHz antenna
gpio_switch(16,1)

# Setup SDR
sdr = sdr_control(freq)

# Collect Data    
spectrum2, faxis2, samples2 = data(sdr)

# Detect Peaks   
amp_peak_12, freq_peak_12, amp_peak_22, freq_peak_22, amp_peak_32, freq_peak_32, amp_peak_42, freq_peak_42, amp_peak_52, freq_peak_52, indexes2 = peak_det(spectrum2, faxis2)

# Get current time and date     
current_date, current_hour, current_time, time_for_save = time_date()

# Save the sampled data for later use if needed 
raw_save(time_for_save,freq_mhz,sdr.sample_rate,samples2)

# Record results
display_write(current_date, current_hour, amp_peak_12, freq_peak_12, amp_peak_22, freq_peak_22, amp_peak_32, freq_peak_32, amp_peak_42, freq_peak_42, amp_peak_52, freq_peak_52)

# Disconnect SDR
sdr.close()

# Deactivate 868MHz antenna
gpio_switch(16,0)

# Flash status lights to indicate successful completion
gpio_switch([22,24,26],1)
gpio_switch([22,24,26],0)

# gpio disconnect
try:
    gpio.cleanup()
except:
    print("GPIO Not Deactivated")

# Plot FFT's 
debug_graph(faxis,spectrum,indexes,faxis2,spectrum2,indexes2)