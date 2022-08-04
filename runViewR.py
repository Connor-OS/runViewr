from cProfile import run
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import image
import gpxpy
from os import listdir
from matplotlib.animation import FuncAnimation
from matplotlib import animation
import pandas as pd
from itertools import count
# import cartopy
# import cartopy.crs as ccrs
# from cartopy.io.img_tiles import OSM

index = count()

map = image.imread('newcastle_large.png')
points = [-1.6574,54.9981,-1.5825,54.9598]
gps_files = listdir('./GPS-data')
run_data = np.empty((len(gps_files),),dtype=object)
for i,v in enumerate(run_data):
    run_data[i] = []

f_num = 0
max_len = 0
for file in gps_files:
    print(f"opening file from {file[:10]}")
    lat = []
    long = []
    with open(f'./GPS-data/{file}','r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        for track in gpx.tracks:
            for seg in track.segments:
                for p in seg.points:
                    long = (p.longitude-points[0])*(map.shape[1]/(points[2]-points[0]))
                    lat = -(p.latitude-points[1])*(map.shape[0]/(points[1]-points[3]))
                    run_data[f_num].append((long,lat))
    if len(run_data[f_num]) > max_len: max_len = len(run_data[f_num])
    f_num += 1
# plt.imshow(map)

def animate(i):
    plt.cla()
    i = next(index)
    for run in run_data:
        plt.plot(*zip(*run[:i]))
    plt.imshow(map)


def main():
    ani = FuncAnimation(plt.gcf(), animate, interval = 5,save_count=max_len)
    # plt.imshow(map)
    print('saving animation...')
    writervideo = animation.FFMpegWriter(fps=60) 
    ani.save("reduce_res.gif", writer=writervideo)
    # plt.show()
    # plt.savefig('prac.png')
    

if __name__ == "__main__":
    main()