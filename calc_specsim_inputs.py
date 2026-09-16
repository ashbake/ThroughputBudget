# uses cThroughput to load excel sheet with throughput files
# then step through and computer the emissivity
# the emissivity is calculated as T + R + ε = 1
# ε = 1 - T - R
import matplotlib.pylab as plt
import numpy as np

from cThroughput import CalcThroughput

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

###########################
data_path   = './inputs/'
save_path    = './outputs/specsim/'
excel_file = './HISPEC_allsubs.xlsx'
tracking_band = 'jhgap'
############################

# Define yJHK band passes for plotting
wave_array = np.arange(920, 2550, 0.1)
yJ = [980,1327]
HK = [1490,2460]

#define include_inds for picking the tracking band
include_ind_dic = {}
include_ind_dic['jhgap'] = 2 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['j'] = 3 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['h'] = 4 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['j+h'] = 5 # 1: jhgap, 2: j, 3: h, 4: j+h


if __name__=='__main__':
    gbt = CalcThroughput(wave_array, './HISPEC_allsubs.xlsx',data_path='./inputs/')

    # ATC Throughput
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']
    label    = 'ATC Throughpu J+H'
    gbt.run(atc_keys, save_path=save_path,label=label, include_ind=include_ind_dic['j+h'])
    gbt.plotSubsections(keys=atc_keys)

    # BSPEC Throughput (minus coupling)
    bspec_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI BLUE', 'FIBER TRANSMISSION BLUE', 'BSPEC']
    label    = 'BSPEC no coupling'
    gbt.run(bspec_keys, save_path=save_path, label=label, include_ind=include_ind_dic[tracking_band])
    gbt.plotSubsections(keys=bspec_keys)
    gbt.plotBackground()
    
    # RSPEC Throughput (minus coupling)
    rspec_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI RED', 'FIBER TRANSMISSION RED', 'RSPEC']
    label      = 'RSPEC no coupling'
    gbt.run(rspec_keys, save_path=save_path,label=label, include_ind=include_ind_dic[tracking_band])
    gbt.plotSubsections(keys=rspec_keys)
    gbt.plotBackground()

	# ^^ Need to splice these together to generate final files for specsim
    # ATC throughput is for one dichroic. choose J+H dichroic so specsim can modify it from there