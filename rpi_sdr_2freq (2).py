## Imports ##
from rtlsdr import RtlSdr
import numpy
import matplotlib.pyplot as plt
import time
import peakutils
import csv
import sys
import gpsd
#from gps3 import gps3
import schedule

try:
    import RPi.GPIO as gpio
    
except:
    print("GPIO Pins Not Available on This Device\n")
 
 
## Function Definitions ##

# def gps_loc():
#             
#     # Attempt to connect to GPS Dongle
#     try:
#         gps_socket = gps3.GPSDSocket()
#         data_stream = gps3.DataStream()
#         
#         gps_socket.connect()
#         gps_socket.watch()
#         
#         # create counter to monitor number of attempts to find location
#         loc_count = 0
#         new_count = 0
#         
#         # wait for new data
#         for new_data in gps_socket:
#             if new_data:
#                 data_stream.unpack(new_data)
#                 
#                 # Find fix mode of device. 2 or 3 indicate lock. 1 is no lock. n/a is unknown     
#                 loc_mode = data_stream.TPV['mode']
#                 
#                 # if fix mode is known
#                 if loc_mode != 'n/a':
#                     #change mode from string to integer
#                     loc_mode = int(loc_mode)
#                     
#                     # If at least 2D fix (mode 2) is achieved, save longitude and latitude with dummy variable for altitude
#                     if loc_mode == 2:
#                         lon = data_stream.TPV['lon']
#                         lat = data_stream.TPV['lat']
#                         alt = 0
#                         break
#                      
#                     # If at 3D fix (mode 3) is achieved, save longitude, latitude and altitude
#                     elif loc_mode == 3:
#                         lon = data_stream.TPV['lon']
#                         lat = data_stream.TPV['lat']
#                         alt = data_stream.TPV['alt']
#                         break
#                     
#                     else:
#                         loc_count += 1
#                     
#                 # If device takes too long to find location, terminate.
#                 elif loc_count > 10:
#                     lon = 0
#                     lat = 0
#                     alt = 0
#                     break
#                 
#                 #advance attempts counter        
#                 else:
#                     loc_count += 1
#         
#             elif new_count > 1000000:
#                 lon = 0
#                 lat = 0
#                 alt = 0
#                 break
#             
#             else:
#                 new_count += 1
#         
#         #disconnect from GPS
#         gps_socket.close()   
#                 
#     # if unable to connect, save dummy variables, alert user and exit
#     except:
#         print('GPS Not Available on This Device\n')
#         lon = 0
#         lat = 0
#         alt = 0
#     
#     return lon, lat, alt

# # Function to read GPS location from a USB GPS dongle
def gps_loc():
       
    # Attempt to connect to GPS Dongle
    try:
        # Connect to the local gpsd
        gpsd.connect()
   
        # Get gps position
        location = gpsd.get_current()
   
        # If at least 2D fix (mode 2 or 3) is achieved, save longitude and latitude
        if location.mode >= 2:
            lon = location.lon
            lat = location.lat
        else:
            lon = 0
            lat = 0
           
        # If at 3D fix (mode 3) is achieved, save altitude
        if location.mode >= 3:
            alt = location.alt
        else:
            alt = 0
       
    # if unable to connect, save dummy variables, alert user and exit
    except:
        print('GPS Not Available\n')
        lon = 0
        lat = 0
        alt = 0
       
    return lon, lat, alt

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
def display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, lon, lat, alt):
    # print first 2 detected peaks
    print('%s %s Peaks: %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz and %.2f dB at %.3f MHz\nLocation: Longitude %.3f, Latitude %.3f, Altitude %.3fm\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, lon, lat, alt))

    # write peaks to a text file
    with open("log.txt","a") as f:
        f.write('%s %s Peaks: %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz, %.2f dB at %.3f MHz and %.2f dB at %.3f MHz Location: Longitude %.3f, Latitude %.3f, Altitude %.3fm\n' % (current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, lon, lat, alt))
        
    f.close()

    #write peaks to a .CSV file
    with open('log.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator = '\n')
        writer.writerow([current_date] + [current_hour] + [amp_peak_1] + [freq_peak_1] + [amp_peak_2] + [freq_peak_2] + [amp_peak_3] + [freq_peak_3] + [amp_peak_4] + [freq_peak_4] + [amp_peak_5] + [freq_peak_5] + [lon] + [lat] + [alt])

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
                    
    array_length = len(spectrum)
        
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

# Get Location
def test():
    
    # Find current GPS Location
    lon, lat, alt = gps_loc()
    
    # Set up GPIO
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
    display_write(current_date, current_hour, amp_peak_1, freq_peak_1, amp_peak_2, freq_peak_2, amp_peak_3, freq_peak_3, amp_peak_4, freq_peak_4, amp_peak_5, freq_peak_5, lon, lat, alt)
    
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
    display_write(current_date, current_hour, amp_peak_12, freq_peak_12, amp_peak_22, freq_peak_22, amp_peak_32, freq_peak_32, amp_peak_42, freq_peak_42, amp_peak_52, freq_peak_52, lon, lat, alt)
    
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
    

# Schedule test to run every X minutes
schedule.every(0.5).minutes.do(test)

# Attempt to connect to GPS device
try:
    # Connect to the local gpsd
    gpsd.connect()

# If device is unavailable, alert user.
except:
    print('GPS Not Available on This Device')

# Run Scheduler on constant loop
while True:
    # Check for pending tasks
    schedule.run_pending()
    # Wait X seconds before checking for pending again
    time.sleep(1)
    
    
    