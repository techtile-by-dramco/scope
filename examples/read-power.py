import time
import sys
from pathlib import Path

try:
    from TechtileScope import Scope
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src.TechtileScope import Scope


config = {
    "ip": "192.108.1.219",
    "channels": [1, 2],
}

scope = Scope(config=config)

while True:
    powers_dbm = scope.get_power_dBm(channels=config["channels"])
    for ch, pwr in zip(config["channels"], powers_dbm):
        print(f"CH{ch} channel power: {pwr:.2f} dBm")
    time.sleep(1)
