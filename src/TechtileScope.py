import time  # std module
import pyvisa as visa  # http://github.com/hgrecco/pyvisa
import numpy as np  # http://www.numpy.org/
from scipy.signal import find_peaks

from enum import Enum


class ScopeMode(Enum):
    # TODO
    POWER = 1


class Scope:
    """_summary_

    Usage:
        scope = Scope("192.108.0.251")
        power_dBm = scope.get_power_dBm()
    """

    def __init__(
        self, ip: str = None, mode: ScopeMode = ScopeMode.POWER, config=None
    ) -> None:

        if ip is None:
            if config is None or "ip" not in config:
                print(
                    "Please provide or an IP address or a config with an IP address specified (key = ip)"
                )
                exit()
            else:
                ip = config["ip"]
        self.visa_address = f"TCPIP::{ip}::INSTR"

        self.span = None

        if config:
            print(f"Setting with following config: {config}")
            self.setup(config)
        else:
            print(
                "No configuration provided, please use the setup method to ocnfigure the scope."
            )

    def write(self, s: str):
        self.scope.write(s)

    def query(self, s: str):
        return self.scope.query(s)

    def get_data(self) -> float:
        return self.scope.query_binary_values(
            "CURVe?", datatype="d", container=np.array
        )

    def setup(self, config):

        bandwidth=config["bandwidth_hz"]
        center=config["center_hz"]
        span=config["span_hz"]
        rbw=config["rbw_hz"]
        termination:int = config["termination"]
        spectrum_view: bool = config["spectrum_view"]

        self.span = span
        self.rbw = rbw

        rm = visa.ResourceManager()
        self.scope = rm.open_resource(self.visa_address)
        self.scope.timeout = 10000  # ms
        self.scope.encoding = "latin_1"
        self.scope.read_termination = "\n"
        self.scope.write_termination = None
        self.scope.write("*cls")  # clear ESR
        self.scope.write("*rst")  # reset
        r = self.scope.query("*opc?")  # sync

        self.scope.query("*idn?")

        # Channel 1 50Ohm 2GHz
        self.scope.write(f"CH1:TERMINATION {termination}")
        self.scope.write(f"CH1:BANDWIDTH {bandwidth}")

        # TODO check if all settings are stored correctly

        self.scope.query(":CH1:TERMINATION?")
        self.scope.query(":CH1:BANdwidth?")

        # Open spectrum view
        # spectrum view 910MHz and 100kHz BW
        if spectrum_view:
            self.scope.write("DISplay:SELect:SPECView1:SOUrce CH1")
            self.scope.write("CH1:SV:STATE ON")
            self.scope.write(f"CH1:SV:CENTERFrequency {center}")
            self.scope.write(f"SV:SPAN {self.span}")

            self.scope.write("SV:RBWMode MANUAL")
            self.scope.write(f"SV:RBW {self.rbw}")

            self.scope.write("SV:CH1:UNIts DBM")

            self.scope.write("DATa:SOUrce CH1_SV_NORMal")

        self.scope.query("DATa:SOUrce?")

        data_stop = round(self.span / self.rbw * 2)

        self.scope.write("DATa:START 1")
        self.scope.write(f"DATa:STOP {data_stop}")

        self.scope.query("DATa:STARt?")
        self.scope.query("DATa:STOP?")

        time.sleep(2)

        print(self.scope.query("WFMOutpre:SPAN?"))
        self.scope.write("WFMOutpre:BYT_Or LSB")

        self.scope.query("DATA:WIDTH?")
        self.scope.query(":WFMOutpre?")

        print(self.scope.query("WFMOutpre:NR_Pt?"))

    def calc_full_channel_power(self, data) -> float:
        # pwr_lin = 10 ** (data / 10)
        # tot_pwr_dbm = float(10*np.log10(np.sum(pwr_lin))) #float to cast to single element
        # return tot_pwr_dbm + self.cable_loss

        # Convert dBm to Watts
        power_samples_W = 10 ** (data / 10) * 1e-3  # Convert dBm to Watts

        # Integrate power samples over the frequency band (each sample corresponds to the RBW)
        total_power_W = np.sum(power_samples_W)

        # Convert total power back to dBm
        total_power_dBm = 10 * np.log10(total_power_W / 1e-3)

        return total_power_dBm

        # print(f"Total channel power: {total_power_dBm:.2f} dBm")

    def calc_channel_power_peaks(self, data, search_for_no_peaks) -> float:

        #   Check span adjustments externally
        self.check_span()

        #   Get spectrum form scope
        pwr_dbm = self.scope.query_binary_values(
            "CURVe?", datatype="d", container=np.array
        )

        #   Calculate all peaks in spectrum
        peaks, _ = find_peaks(pwr_dbm)
        # print(pwr_dbm[peaks])

        #   Sort peaks in descending order
        peaks_sorted = sorted(pwr_dbm[peaks], reverse=True)
        # print(peaks_sorted[:search_for_no_peaks])

        #   Combine peaks to one overall power value
        power_linear = 10 ** (np.asarray(peaks_sorted[:search_for_no_peaks]) / 10)
        # print(power_linear)
        tot_pwr_dbm = float(
            10 * np.log10(np.sum(power_linear))
        )  # float to cast to single element
        return tot_pwr_dbm, peaks

    def check_span(self):
        new_span = float(self.query(f"SV:SPAN?"))
        if new_span != self.span:

            #   Warning
            print("Span changed externally!")

            #   Update span value
            self.span = new_span

            data_stop = round(self.span / self.rbw * 2)

            self.write(f"DATa:START 1")
            self.write(f"DATa:STOP {data_stop}")  # 1901

    def get_power_dBm(self) -> float:
        pwr_data_dbm = self.get_data()
        tot_pwr_dbm, peaks = self.calc_channel_power_peaks(pwr_data_dbm, 1)
        return tot_pwr_dbm

    def get_power_dBm_peaks(self, search_for_no_peaks, cable_loss=None) -> float:

        #   Check span adjustments externally
        self.check_span()

        #   Get spectrum form scope
        pwr_dbm = self.scope.query_binary_values(
            "CURVe?", datatype="d", container=np.array
        )

        #   Calculate all peaks in spectrum
        peaks, _ = find_peaks(pwr_dbm)
        # print(pwr_dbm[peaks])

        #   Sort peaks in descending order
        peaks_sorted = sorted(pwr_dbm[peaks], reverse=True)
        print(peaks_sorted[:search_for_no_peaks])

        #   Combine peaks to one overall power value
        power_linear = 10 ** (np.asarray(peaks_sorted[:search_for_no_peaks]) / 10)
        # print(power_linear)
        tot_pwr_dbm = float(
            10 * np.log10(np.sum(power_linear))
        )  # float to cast to single element
        if cable_loss is None:
            cable_loss = 0
            print("no cabling loss taken into account")
        return tot_pwr_dbm + cable_loss, peaks

    def check_span(self):
        new_span = float(self.query("SV:SPAN?"))
        if new_span != self.span:

            #   Warning
            print("Span changed externally!")

            #   Update span value
            self.span = new_span

            data_stop = round(self.span / self.rbw * 2)

            self.write("DATa:START 1")
            self.write(f"DATa:STOP {data_stop}")  # 1901
