import time  # std module
import logging
import sys
import pyvisa as visa  # http://github.com/hgrecco/pyvisa
import numpy as np  # http://www.numpy.org/
from scipy.signal import find_peaks

from enum import Enum


class ScopeMode(Enum):
    # TODO
    POWER = 1


ANSI_RESET = "\x1b[0m"
ANSI_CYAN = "\x1b[36m"
ANSI_YELLOW = "\x1b[33m"
ANSI_GREEN = "\x1b[32m"


class Scope:
    """_summary_

    Usage:
        scope = Scope("192.108.0.251")
        power_dBm = scope.get_power_dBm()
    """

    def __init__(
        self,
        ip: str = None,
        mode: ScopeMode = ScopeMode.POWER,
        config=None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(f"{__name__}.Scope")
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        self.mode = mode

        if ip is None:
            if config is None or "ip" not in config:
                self.logger.error(
                    "Please provide or an IP address or a config with an IP address specified (key = ip)"
                )
                exit()
            else:
                ip = config["ip"]
        self.visa_address = f"TCPIP::{ip}::INSTR"

        self.span = None

        if config:
            self.logger.info("Setting with following config: %s", config)
            self.setup(config)
        else:
            self.logger.warning(
                "No configuration provided, please use the setup method to ocnfigure the scope."
            )

    def scope_write(self, s: str):
        self.logger.debug("%sSCPI write%s: %s", ANSI_CYAN, ANSI_RESET, s)
        self.scope.write(s)

    def write(self, s: str):
        self.scope_write(s)

    def scope_query(self, s: str):
        self.logger.debug("%sSCPI query%s: %s", ANSI_YELLOW, ANSI_RESET, s)
        result = self.scope.query(s)
        self.logger.debug(
            "%sSCPI result%s: %s -> %s", ANSI_GREEN, ANSI_RESET, s, result
        )
        return result

    def query(self, s: str):
        return self.scope_query(s)

    def get_data(self) -> float:
        return self.scope.query_binary_values(
            "CURVe?", datatype="d", container=np.array
        )

    def setup(self, config):

        bandwidth = config.get("bandwidth_hz", 2e9)
        center = config.get("center_hz", 920e6)
        span = config.get("span_hz", 100e3)
        rbw = config.get("rbw_hz", 20)
        termination: int | None = config.get("termination", 50)
        spectrum_view: bool | None = config.get("spectrum_view", True)
        channels: bool | None = config.get("channels", 1)

        rm = visa.ResourceManager()
        self.scope = rm.open_resource(self.visa_address)
        self.scope.timeout = 10000  # ms
        self.scope.encoding = "latin_1"
        self.scope.read_termination = "\n"
        self.scope.write_termination = None
        self.scope_write("*cls")  # clear ESR
        self.scope_write("*rst")  # reset
        r = self.scope_query("*opc?")  # sync

        self.scope_query("*idn?")

        # Channel 1 50Ohm 2GHz
        if termination is not None:
            self.scope_write(f"CH1:TERMINATION {termination}")
        if bandwidth is not None:
            self.scope_write(f"CH1:BANDWIDTH {bandwidth}")

        # Open spectrum view
        # spectrum view 910MHz and 100kHz BW

        for c in channels:
            self.scope_write(f"DISplay:SELect:SPECView1:SOUrce CH{c}")
            self.scope_write(f"CH{c}:SV:STATE ON")
            self.scope_write(f"CH{c}:SV:CENTERFrequency {center}")
            self.scope_write(f"SV:SPAN {span}")
            self.scope_write("SV:RBWMode MANUAL")
            self.scope_write(f"SV:RBW {rbw}")
            self.scope_write(f"SV:CH{c}:UNIts DBM")
            self.scope_write(f"DATa:SOUrce CH{c}_SV_NORMal")

        time.sleep(2)

        self.logger.info("WFMOutpre:SPAN? -> %s", self.scope_query("WFMOutpre:SPAN?"))
        self.scope_write("WFMOutpre:BYT_Or LSB")

        self.scope_query("DATA:WIDTH?")
        self.scope_query(":WFMOutpre?")

        self.scope_query("WFMOutpre:NR_Pt?")

        time.sleep(1)

        if self.mode == ScopeMode.POWER:

            for c in channels:
                self.scope_write(f"MEASUREMENT:MEAS{c}:TYPE CPOWER")

                self.scope_write(f"MEASUREMENT:MEAS{c}:SOUrce CH{c}_SV_NORMal")

                self.logger.info(
                    "MEASUREMENT:MEASRange:STATE? -> %s",
                    self.scope_query("MEASUREMENT:MEASRange:STATE?"),
                )

                self.scope_write(f"MEASUREMENT:MEAS{c}:CPWIDTh 5E+3")

                self.logger.info(
                    "MEASUREMENT:MEAS%d:CPWIDTh? -> %s",
                    c,
                    self.scope_query(f"MEASUREMENT:MEAS{c}:CPWIDTh?"),
                )

        self.scope_write("*WAI")

    def get_power_Watt(self, channels: list[int]=[1]) -> float:
        vals = []
        for c in channels:
            val = float(self.scope_query(f"measurement:meas{c}:subgroup:results:currentacq:mean? 'channelpower'"))
            vals.append(float(val))
        return np.asarray(vals)

    def get_power_dBm(self, channels: list[int]=[1]) -> float:
        return 10 * np.log10(self.get_power_Watt(channels) / 1e-3)
