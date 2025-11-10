import time # std module
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import numpy as np # http://www.numpy.org/
from scipy.signal import find_peaks

from enum import Enum

ip = "192.108.1.219"

rm = visa.ResourceManager()
scope = rm.open_resource(f'TCPIP::{ip}::INSTR')

scope.write('*rst') # reset

# Add new measurement phase
for i in range(3):
  scope.write("MEASUREMENT:ADDMEAS PHASE")

# Query list of measurements
meas_list = scope.query("MEASUrement:LIST?")
meas_list = meas_list.replace('\n', '').split(',')

# Define channels (phase measurment)
channel_1 = "CH1"
channel_2 = "CH2"
channel_3 = "CH3"
channel_4 = "CH4"

channels = [channel_1, channel_2, channel_3, channel_4]

for i in range(4):
  scope.write(f"{channels[i]}:TERMINATION 50")
  scope.write(f"{channels[i]}:BANdwidth 2e9")
  # scope.write(f"DISplay:GLObal:PLOT{i}:STATE ON")
  scope.write(f"SELECT:{channels[i]} 1")

scope.write("HORIZONTAL:MODE:SCALE 400e-12")
scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")


# Update sources from last added measurement
for i in range(3):
  scope.write(f"MEASUrement:{meas_list[i]}:SOUrce1 {channel_1}")
  scope.write(f"MEASUrement:{meas_list[i]}:SOUrce2 {channels[i+1]}")

while 1:

  measurements = scope.query("MEASUrement:LIST?").replace('\n', '').split(',')

  for meas in measurements:
    res = scope.query(f"MEASUrement:{meas}:RESUlts:HISTory:MEAN?")
    print(f"{meas}: {res}", end="")
  
  print()

  time.sleep(1)