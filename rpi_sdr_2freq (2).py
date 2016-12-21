# imports
from rtlsdr import RtlSdr
import numpy
import matplotlib.pyplot as plt
import time
import peakutils
import csv

# Function to produce strings with time and date
def time_date():
    # string including data and time
    current_time = time.strftime("%d/%m/%y %H:%M:%S")
    # string with just date
    current_date = time.strftime("%d/%m/%y")
    # string with just time
    current_hour = time.strftime("%H:%M:%S")
    
    return current_date, current_hour, current_time

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
    
    return amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, indexes

# Function to display results and write to a .CSV and .TXT file
def display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2):
    # print first 2 detected peaks
    print('%s %s Peaks: %.2f dB at %.3f MHz and %.2f dB at %.3f MHz\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2))
        
    # write peaks to a text file
    with open("log.txt","a") as f:
        f.write('%s %s Peaks: %.2f dB at %.3f MHz and %.2f dB at %.3f MHz\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2))
        
    #write peaks to a .CSV file
    with open('log.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
        writer.writerow([current_date] + [current_hour] + [amp_peak_1] + [freq_peak_1] + [amp_peak_2] + [freq_peak_2])

# Function to get samples and create FFT
def data(sdr):
    # Read in samples from the device
    samples = sdr.read_samples(5000)
            
    # now process fft
    spectrum = 20 * numpy.log10(abs(numpy.fft.fft(samples)))
    print ("fft ready")
                    
    array_length = len(samples)
        
    # create frequency axis, noting that Fc is in centre
    fstep = sdr.sample_rate/len(spectrum) # fft bin size
    fstep = fstep / 1000000 #  convert to MHz
        
    faxis = []
    k = 0
    while k < array_length:
        faxis.append((sdr.center_freq/1000000) + k * fstep)
        k = k + 1

    return spectrum, faxis

#function to set up and configure SDR
def sdr_control(freq):

    # Create device
    sdr = RtlSdr()

    # configure device
    sdr.sample_rate = 2.048e6  # Hz
    sdr.center_freq = freq   # Hz
    sdr.gain = 'auto'
        
    return sdr

# Set first frequency of interest and display in MHz
freq = 70e6
freq_mhz = freq/1000000
print("Sampling at %.2f MHz\n" % freq_mhz)

# Set up SDR
sdr = sdr_control(freq)

# Collect Data  
spectrum, faxis = data(sdr)

# Detect Peaks   
amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, indexes = peak_det(spectrum, faxis)

# Get current time and date    
current_date, current_hour, current_time = time_date()

# Record results
display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2)

# Disconnect SDR
sdr.close()
    
# Taking second sample

# Set second frequency of interest and diplay in MHz
freq = 868e6
freq_mhz = freq/1000000
print("Sampling at %.2f MHz\n" % freq_mhz)

# Setup SDR
sdr = sdr_control(freq)

# Collect Data    
spectrum2, faxis2 = data(sdr)

# Detect Peaks   
amp_peak_12, freq_peak_12, amp_peak_22, freq_peak_22, indexes2 = peak_det(spectrum2, faxis2)

# Get current time and date     
current_date, current_hour, current_time = time_date()

# Record results
display_write(current_date, current_hour, amp_peak_12, freq_peak_12, amp_peak_22, freq_peak_22)

# Disconnect SDR
sdr.close()


# graph data to aid debuging
# plot the date from the last sample period
plt.plot(faxis,spectrum.real)

# Plot all detected peaks
x = 0
while x < len(indexes):
    plt.plot(faxis[indexes[x]], spectrum.real[indexes[x]], 'ro')
    x += 1

# format plot
plt.xlabel('MHz')
plt.ylabel('dB')
plt.title('FFT of spectrum')
plt.grid()

plt.figure()
# plot the date from the last sample period
plt.plot(faxis2,spectrum2.real)

# Plot all detected peaks
x = 0
while x < len(indexes2):
    plt.plot(faxis2[indexes2[x]], spectrum2.real[indexes2[x]], 'ro')
    x += 1

# format plot
plt.xlabel('MHz')
plt.ylabel('dB')
plt.title('FFT of spectrum')
plt.grid()
plt.show()
