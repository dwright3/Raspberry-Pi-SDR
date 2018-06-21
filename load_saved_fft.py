'''
Created on 7 Jun 2018

@author: elp15dw
'''

import numpy
import matplotlib.pyplot as plt
import glob
import csv
from math import radians, sin, cos, sqrt, asin

def haversine(lat1, lon1, lat2, lon2):
 
    R = 6372.8 # Earth radius in kilometers
     
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
     
    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
     
    return R * c *1000

snr_level = 5

freq_offset = 0.1
peak_search_range = 0.05

origin_lat = 53.380834
origin_lon = -1.478466

data = []

#open csv file and load results
with open('C:/Users\elp15dw\Google Drive\Tests\Test 08.05.18\log.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
           
        data.append(row[0:14]) 
        
        
csvfile.close()



time = []
date = []
peak_1_amp = []
peak_2_amp = []
peak_3_amp = []
peak_4_amp = []
noise_amp = []
peak_1_freq = []
peak_2_freq = []
peak_3_freq = []
peak_4_freq = []
file_name = []
snr = []
lat = []
lon = []
dist = []

# separate data in to useful variables
for line in data:
    
    date = line[0]
    day = date[0:2]
    month = date[3:5]
    year = date[8:10]
    
         
    time = line[1]
    hour = time[0:2]
    minute = time[3:5]
    sec = time[6:8]
    
    
    sig = float(line[2]) - 144
    noise = float(line[10]) - 144
    
    lat = float(line[13])
    lon = float(line[12])
        
    curr_snr = sig - noise
    
    x = 0 
   
    if lon == 0:
        
        curr_dist = 0
        
    else:
        curr_dist = haversine(origin_lat, origin_lon, lat, lon)
    

    
    #search for required data 
    if  curr_snr > 5 and curr_snr < 10 and curr_dist > 200:
            
        peak_1_amp.append(float(line[2]))
        peak_2_amp.append(float(line[4]))
        peak_3_amp.append(float(line[6]))
        peak_4_amp.append(float(line[8]))
        noise_amp.append(float(line[10]))
    
        peak_1_freq.append(float(line[3]))
        peak_2_freq.append(float(line[5]))
        peak_3_freq.append(float(line[7]))
        peak_4_freq.append(float(line[9]))
        
        snr.append(curr_snr)
        
        dist.append(curr_dist)        
        
        file_name.append('C:/Users\elp15dw\Google Drive\Tests\Test ' + day + '.' + month + '.'  + year + '\\' + '*' + month + '_' + day + '_'  + year + '-' + hour + '_' + minute  + '_' + sec + '*.npy')
        

titles = []
sample_rate_str = []
center_freq_str = []
samples = []

#load .npy files for required dta
for name in file_name:
        
    curr_file = glob.glob(name)
    
    print(curr_file[0])
    
    #split file path to extract file name
    curr_file_name = curr_file[0].split('\\')
    
    #split file name in to constituent parts to retrieve info
    info = curr_file_name[-1].split('-')
    
    #convert date to readable format
    date = info[0].replace('_','.')
    #convert time to readable format
    time = info[1].replace('_',':')
    
    # Create title for plots
    titles.append(date + ' ' + time + ' ' + info[2])
    
    #retrieve sample rate
    sample_rate_str.append(info[3][:-3])
    #retrieve centre frequency
    center_freq_str.append(info[2][:-3])
    
    samples.append(numpy.load(curr_file[0]))
    
num_samples = len(samples)
print("\n%d Sample Files Loaded\n" % num_samples)


faxis = []

x = 0 

#reconstruct frequency axis
for index in samples: 
         
    array_length = len(index)
 
    sample_rate = float(sample_rate_str[x])
    center_freq = float(center_freq_str[x])
    
    if center_freq == 71.0:
        center_freq = center_freq + 0.1
        
    elif center_freq == 869.5:
        center_freq = center_freq + 0.125
        
    else:
        center_freq = center_freq + 0.1
 
    # create frequency axis, noting that Fc is in centre
    fstep = sample_rate/array_length # fft bin size
        
    curr_faxis = []
    
    k = 0
    while k < array_length:
        curr_faxis.append(((center_freq)-(fstep*(array_length/2))) + k * fstep)
        k = k + 1
        
    faxis.append(curr_faxis)
    
    x = x + 1
 
print ("FFT Ready\n")

x = 0

# plot the saved ffts
for index in samples:
    
    plt.figure()
    plt.plot(faxis[x],index-144, label='Received Power')
    
    #plot recorded peaks
    plt.plot(peak_1_freq[x], peak_1_amp[x]-144, 'go', label = 'Detected Peaks')
    plt.plot(peak_2_freq[x], peak_2_amp[x]-144, 'go')
    plt.plot(peak_3_freq[x], peak_3_amp[x]-144, 'go')
    plt.plot(peak_4_freq[x], peak_4_amp[x]-144, 'go')
    
    #plot estimated noise
    plt.plot([faxis[x][0],faxis[x][4999]],[(noise_amp[x]-144),(noise_amp[x]-144)], 'r--',linewidth=5, label = 'Estimated Noise Level')
    
    # annotate plot with highest peak
    plt.annotate('recorded Peak Power \n %.1f dBm \n %.3f MHz'%((peak_1_amp[x]-144), peak_1_freq[x]),
        xy=(peak_1_freq[x], (peak_1_amp[x]-144)), xycoords='data',
        xytext=(0.65, 0.75), textcoords='figure fraction',
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        
    # annotate plot with noise value    
    plt.annotate('Recorded Estimated Noise: \n %.1f dBm \n Recorded SNR: \n %.1f dBm \n Recorded Distance From TX: \n %.1f m' %((noise_amp[x]-144), snr[x], dist[x]),
        xy=(faxis[x][2500], (noise_amp[x]-144)), xycoords='data',
        xytext=(0.15, 0.5), textcoords='figure fraction')

    
    axes = plt.gca()
    ymin, ymax = axes.get_ylim()
    plt.plot([(faxis[x][2500]-peak_search_range-freq_offset),(faxis[x][2500]-peak_search_range-freq_offset)],[ymax,ymin], 'k:',linewidth=2.5, label = 'Peak search Limits')
    plt.plot([(faxis[x][2500]+peak_search_range-freq_offset),(faxis[x][2500]+peak_search_range-freq_offset)],[ymax,ymin], 'k:',linewidth=2.5)
    
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Relative Power (dB)')
    plt.title(titles[x])
    plt.legend(loc='upper left',fontsize ='small')
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.grid()
 
    x = x + 1
 
plt.show()
