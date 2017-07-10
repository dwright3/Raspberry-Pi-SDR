import csv
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as md


data = dict()

x = 1

with open('C:/Users\elp15dw\Google Drive\Tests\Test 15.06.17\log.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
           
        data[x] = row[1:12]
        
        x += 1
        
csvfile.close()

x = 1
time_70 = []
time_868 = []
peak_1_amp_70 = []
peak_2_amp_70 = []
peak_3_amp_70 = []
peak_4_amp_70 = []
peak_5_amp_70 = []
peak_1_amp_868 = []
peak_2_amp_868 = []
peak_3_amp_868 = []
peak_4_amp_868 = []
peak_5_amp_868 = []

freq_check = 500

for line in data:
    
    time = data[x][0]
    hour = int(time[0:2])
    minute = int(time[3:5])
    sec = int(time[6:8])
    time_2 = datetime.datetime(2017,6,15,hour,minute,sec)
    peak_1 = float(data[x][1])
    peak_2 = float(data[x][3])
    peak_3 = float(data[x][5])
    peak_4 = float(data[x][7])
    peak_5 = float(data[x][9])
    
    if float(data[x][2]) < freq_check:
        time_70.append(time_2)
        peak_1_amp_70.append(peak_1)
        peak_2_amp_70.append(peak_2)
        peak_3_amp_70.append(peak_3)
        peak_4_amp_70.append(peak_4)
        peak_5_amp_70.append(peak_5)
        
    else:
        time_868.append(time_2)
        peak_1_amp_868.append(peak_1)
        peak_2_amp_868.append(peak_2)
        peak_3_amp_868.append(peak_3)
        peak_4_amp_868.append(peak_4)
        peak_5_amp_868.append(peak_5)
    
    x = x+1
    
    
x = 0

xfmt = md.DateFormatter('%d-%m-%Y %H:%M:%S')

plt.figure(1)

#plt.subplot(211)
plt.plot(time_70, peak_1_amp_70,'o-', label="Highest Peak")
plt.plot(time_70, peak_2_amp_70,'o-', label="2nd Highest Peak")
plt.plot(time_70, peak_3_amp_70,'o-', label="3rd Highest Peak")
plt.plot(time_70, peak_4_amp_70,'o-', label="4th Highest Peak")
plt.plot(time_70, peak_5_amp_70,'o-', label="5th Highest Peak")
plt.xlabel('Time (GMT)')
plt.ylabel('Relative Power (dB)')
plt.title('71MHz Detected Peak Powers Against Time')
plt.minorticks_on()
plt.grid(which='both', axis='both')
plt.gca().xaxis.set_major_formatter(xfmt)
plt.legend()

plt.figure(2)
#plt.subplot(212)
plt.plot(time_868, peak_1_amp_868,'o-', label="Highest Peak")
plt.plot(time_868, peak_2_amp_868,'o-', label="2nd Highest Peak")
plt.plot(time_868, peak_3_amp_868,'o-', label="3rd Highest Peak")
plt.plot(time_868, peak_4_amp_868,'o-', label="4th Highest Peak")
plt.plot(time_868, peak_5_amp_868,'o-', label="5th Highest Peak")
plt.xlabel('Time (GMT)')
plt.ylabel('Relative Power (dB)')
plt.title('869MHz Detected Peak Powers Against Time')
plt.minorticks_on()
plt.grid(which='both', axis='both')
plt.gca().xaxis.set_major_formatter(xfmt)

plt.legend()
plt.show()




