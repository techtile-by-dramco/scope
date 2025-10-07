
import time
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import numpy as np

ip = "192.108.1.219"
bandwidth = 2e9
center = 1000e6
span = 100e3
rbw = 20

rm = visa.ResourceManager()
scope = rm.open_resource(f'TCPIP::{ip}::INSTR')
scope.timeout = 10000 # ms
scope.encoding = 'latin_1'
scope.read_termination = '\n'
scope.write_termination = None
scope.write('*cls') # clear ESR
scope.write('*rst') # reset
r = scope.query('*opc?') # sync

scope.query('*idn?')

# Channel 1 50Ohm 2GHz
scope.write("CH1:TERMINATION 50")
scope.write(f"CH1:BANDWIDTH {bandwidth}")

# scope.query(':CH1:TERMINATION?')
# scope.query(':CH1:BANdwidth?')

# Channel 2 50Ohm 2GHz
scope.write("CH2:TERMINATION 50")
scope.write(f"CH2:BANDWIDTH {bandwidth}")


# Open spectrum view
# spectrum view 910MHz and 100kHz BW
scope.write("DISplay:SELect:SPECView1:SOUrce CH1")
scope.write("CH1:SV:STATE ON")
scope.write(f"CH1:SV:CENTERFrequency {center}")
scope.write(f"SV:SPAN {span}")

scope.write("SV:RBWMode MANUAL")
scope.write(f"SV:RBW {rbw}")

scope.write("SV:CH1:UNIts DBM")

scope.write("DATa:SOUrce CH1_SV_NORMal")

# scope.query("DATa:SOUrce?")

# data_stop = round(span/rbw*2)

# scope.write("DATa:START 1")
# scope.write(f"DATa:STOP {data_stop}")

# scope.query("DATa:STARt?")
# scope.query("DATa:STOP?")

# Channel 2
scope.write("DISplay:SELect:SPECView1:SOUrce CH2")
scope.write("CH2:SV:STATE ON")
scope.write(f"CH2:SV:CENTERFrequency {center}")
scope.write(f"SV:SPAN {span}")
scope.write("SV:RBWMode MANUAL")
scope.write(f"SV:RBW {rbw}")
scope.write("SV:CH2:UNIts DBM")
scope.write("DATa:SOUrce CH2_SV_NORMal")

time.sleep(2)

print(scope.query("WFMOutpre:SPAN?"))
scope.write("WFMOutpre:BYT_Or LSB")

scope.query("DATA:WIDTH?")
scope.query(":WFMOutpre?")

print(scope.query("WFMOutpre:NR_Pt?"))

time.sleep(1)

# Measurement 1
scope.write("MEASUREMENT:MEAS1:TYPE CPOWER")

scope.write("MEASUREMENT:MEAS1:SOUrce CH1_SV_NORMal")

print(scope.query("MEASUREMENT:MEASRange:STATE?"))

scope.write("MEASUREMENT:MEAS1:CPWIDTh 5E+3")

print(scope.query("MEASUREMENT:MEAS1:CPWIDTh?"))


# Measurement 2
scope.write("MEASUREMENT:MEAS2:TYPE CPOWER")

scope.write("MEASUREMENT:MEAS2:SOUrce CH2_SV_NORMal")

print(scope.query("MEASUREMENT:MEASRange:STATE?"))

scope.write("MEASUREMENT:MEAS2:CPWIDTh 5E+3")

print(scope.query("MEASUREMENT:MEAS2:CPWIDTh?"))


# time.sleep(0.1)
scope.write("*WAI")



while 1:
  time.sleep(1)
  
  # Read Meas 1
  meas1 = scope.query("measurement:meas1:subgroup:results:currentacq:mean? 'channelpower'")
  print(f"Read Channel Power [dBm] - MEAS 1: {10 * np.log10(float(meas1)/1e-3)}")

  meas2 = scope.query("measurement:meas2:subgroup:results:currentacq:mean? 'channelpower'")
  print(f"Read Channel Power [dBm] - MEAS 2: {10 * np.log10(float(meas2)/1e-3)}")
