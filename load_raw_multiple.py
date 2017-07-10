
import numpy
import matplotlib.pyplot as plt
import glob

samples = dict()
names = dict()
titles = dict()
sample_rate_str = dict()
center_freq_str = dict()

x = 1

for name in glob.glob('C:/Users\elp15dw\Google Drive\Tests\Test 15.06.17\*.npy'):
    print (name)
    
    #split file path to extract file name
    file_name = name.split('\\')
    
    #split file name in to constituent parts to retrieve info
    info = file_name[-1].split('-')
    
    #convert date to readable format
    date = info[0].replace('_','.')
    #convert time to readable format
    time = info[1].replace('_',':')
    
    # Create title for plots
    titles[x] = date + ' ' + time + ' ' + info[2]
    
    #retrieve sample rate
    sample_rate_str[x] = info[3][:-3]
    #retrieve centre frequency
    center_freq_str[x] = info[2][:-3]
    
    samples[x] = numpy.load(name)
    x = x + 1

num_samples = len(samples)
print("\n%d Sample Files Loaded\n" % num_samples)



spectrums = dict()
faxis = dict()

for index in samples: 
    
    # take fft of samples
    fft = numpy.fft.fft(samples[index])
    # shift the fft so Fc is at the centre of the plot
    fft_shift = numpy.fft.fftshift(fft)
    # convert to dB
    spectrums[index] = 20 * numpy.log10(abs(fft_shift)) 
    
    array_length = len(samples[index])

    sample_rate = float(sample_rate_str[index])
    center_freq = float(center_freq_str[index])

    # create frequency axis, noting that Fc is in centre
    fstep = sample_rate/array_length # fft bin size
       
    faxis[index] = []
    k = 0
    while k < array_length:
        faxis[index].append(((center_freq)-(fstep*(array_length/2))) + k * fstep)
        k = k + 1

print ("FFT Ready\n")

for index in spectrums:
    plt.figure()
    plt.plot(faxis[index],spectrums[index].real)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Relative Power (dB)')
    plt.title(titles[index])
    plt.grid()



plt.show()