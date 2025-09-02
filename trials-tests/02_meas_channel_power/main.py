import sys
import os
import time

# # Get the current directory of the script
# server_dir = os.path.dirname(os.path.abspath(__file__))

# print(server_dir)

# # Navigate two folder back to reach the parent directory
# exp_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.join(server_dir, os.pardir)), os.pardir))

# # *** Includes continuation ***
# sys.path.append(f"{exp_dir}/server/scope")
from scope import Scope

# # *** Local includes ***
# sys.path.append(f"{exp_dir}/server")
# from yaml_utils import *

# #   Read YAML file
# config = read_yaml_file(f"{exp_dir}/config.yaml")

# #   INFO
# info = config.get('info', {})

# #   ENERGY PROFILER SYSTEM SETTINGS --> ToDo Check if it is definied in config file
# scope_yaml = config.get('scope', {})

ip = "192.108.1.219"
# ip = "10.128.51.253"
bw = 2e9
center = 920e6
span = 100e3
rbw = 20

scope = Scope(ip, 0)
scope.setup(bw, center, span, rbw, 1)
  # scope_yaml.get("bandwidth_hz"), scope_yaml.get("center_hz"), scope_yaml.get("span_hz"), scope_yaml.get("rbw_hz"), 84)

while 1:
  # print(scope.calc_channel_power_peaks(1)[0])

  print(scope.get_meas_1())
  time.sleep(1)

