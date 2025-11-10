import time # std module
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import numpy as np # http://www.numpy.org/
from scipy.signal import find_peaks

from enum import Enum

import matplotlib.pyplot as plt

ip = "192.108.1.219"

rm = visa.ResourceManager()
scope = rm.open_resource(f'TCPIP::{ip}::INSTR')

scope.write('*rst') # reset

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
# scope.write("HORizontal:FASTframe:MULtipleframes:MODe OVERlay")
scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")


time.sleep(1)

voltages = {}

for i in range(4):
  scope.write(f"DATA:SOURCE {channels[i]}")
  scope.write("DATA:START 1")
  scope.write("DATA:STOP 1000")
  ymult = float(scope.query(":WFMOutpre:YMULT?"))   # volts per bit
  yoff  = float(scope.query(":WFMOutpre:YOFF?"))    # offset in bits
  yzero = float(scope.query(":WFMOutpre:YZERO?"))   # referentie (meestal 0)
  raw = scope.query_binary_values("CURVe?", datatype="b", container=np.array)
  volt = (raw - yoff) * ymult + yzero

  voltages[f"{channels[i]}"] = volt


xincr = float(scope.query(":WFMOutpre:XINCR?"))   # tijd tussen samples
xzero = float(scope.query(":WFMOutpre:XZERO?"))   # tijd van eerste punt
pt_off = float(scope.query(":WFMOutpre:PT_OFF?")) # offset in samples
time = (np.arange(len(volt)) - pt_off) * xincr + xzero

# === Plot ===
plt.figure(figsize=(10, 5))
for i in range(4):  
  plt.plot(time, voltages[f"{channels[i]}"])
plt.xlabel("Tijd [s]")
plt.ylabel("Spanning [V]")
plt.title("Tektronix MSO64B - Golfvormen")
plt.grid(True)
plt.show()

