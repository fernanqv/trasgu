#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 12 22:17:15 2023

@author: pmaresnasarre
"""

import pyvinecopulib as pv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os 


#read data and prepare
data = pd.read_csv('UI-1_ship_and_wake_data_for_TUDelft.csv', parse_dates=True).dropna().reset_index(drop=True)

cols = [3, 4, 7, 9, 21, 26, 29, 30]
selected_data = data.iloc[:, cols]
unity_inbound = pv.to_pseudo_obs(np.array(selected_data))

# Save unity_inbound to a CSV file
np.savetxt('unity_inbound.txt', unity_inbound)