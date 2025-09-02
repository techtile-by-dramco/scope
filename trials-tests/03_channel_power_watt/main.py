
import time
import pyvisa as visa # http://github.com/hgrecco/pyvisa

ip = "192.108.1.219"
bandwidth = 2e9
center = 920e6
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

scope.query(':CH1:TERMINATION?')
scope.query(':CH1:BANdwidth?')

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

scope.query("DATa:SOUrce?")

data_stop = round(span/rbw*2)

scope.write("DATa:START 1")
scope.write(f"DATa:STOP {data_stop}")

scope.query("DATa:STARt?")
scope.query("DATa:STOP?")

time.sleep(2)

print(scope.query("WFMOutpre:SPAN?"))
scope.write("WFMOutpre:BYT_Or LSB")

scope.query("DATA:WIDTH?")
scope.query(":WFMOutpre?")

print(scope.query("WFMOutpre:NR_Pt?"))

time.sleep(1)

scope.write("MEASUREMENT:MEAS1:TYPE CPOWER")

scope.write("MEASUREMENT:MEAS1:SOUrce CH1_SV_NORMal")

print(scope.query("MEASUREMENT:MEASRange:STATE?"))

print(scope.query("MEASUREMENT:MEAS1:CPWIDTh?"))

# Proposed by Massimiliano Fiaschetti
print(f"Read Channel Power - Trial 1: {scope.query("measurement:meas1:subgroup:results:currentacq:mean? 'channelpower'")}")

# Proposed by Massimiliano Fiaschetti
print(f"Read Channel Power - Trial 2: {scope.query("measurement:meas1:subgroup:results:allacqs:mean? 'channelpower'")}")

scope.write("MEASUREMENT:MEAS1:CPWIDTh 5E+3")

print(f"Read Channel Power - Trial 3: {scope.query('MEASUrement:MEAS1:RESUlts:ALLAcqs:MIN?')}")

