import csv
import gmplot

data = dict()

x = 1

with open('C:/Users\elp15dw\Google Drive\Tests\Test 15.06.17\log.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
           
        data[x] = row[-3:]
        
        x += 1
        
csvfile.close()

x = 1
lon = []
lat = []
alt = []

lon_check = 0
lat_check = 0
alt_check = 0

for line in data:
    
    lon_con = float(data[x][0])
    lat_con = float(data[x][1])
    alt_con = float(data[x][2])
    
    if lon_con != 0 and lon_con != lon_check:
        lon.append(lon_con)
    
    if lat_con != 0 and lat_con != lat_check:
        lat.append(lat_con)
        
    if alt_con != 0 and alt_con != alt_check:
        alt.append(alt_con)
    
    x = x+1
    
    lon_check = lon_con
    lat_check = lat_con
    alt_check = alt_con
    
x = 0

gmap = gmplot.GoogleMapPlotter(lat[0], lon[0], 16)

gmap.plot(lat, lon, 'cornflowerblue', edge_width=5)
gmap.scatter(lat, lon, 'red', marker=True)

#for pos in lat:


#    x = x+1

gmap.draw("mymap.html")

print(lon)
print(lat)
print(alt)

