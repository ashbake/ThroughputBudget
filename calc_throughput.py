# uses cThroughput to load throughput of various paths and plot

import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import csv, os
from scipy.interpolate import interp1d
from matplotlib.ticker import MultipleLocator

from cThroughput import CalcThroughput

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

data_path   = './inputs/'
save_path    = './outputs/'
excel_file = '../HISPEC_allsubs.xlsx'
#excel_file   = './HISPEC_gary_version.xlsx'

# Define yJHK band passes for plotting
x = np.arange(920, 2550, 0.05)
yJ = [980,1327]
HK = [1490,2460]

tracking_band = 'j'

#define include_inds for picking the tracking band
include_ind_dic = {}
include_ind_dic['jhgap'] = 2 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['j'] = 3 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['h'] = 4 # 1: jhgap, 2: j, 3: h, 4: j+h
include_ind_dic['j+h'] = 5 # 1: jhgap, 2: j, 3: h, 4: j+h

# initialize class - will load in the excel file and the throughput data for the subsystems
ct = CalcThroughput(x, '../HISPEC_allsubs.xlsx',data_path='./inputs/', include_ind=include_ind_dic[tracking_band])


def noblaze_foraidan():
	# # calc throughputs WITHOUT THE BLAZE - need to go to excel sheet and put a 0 under include column for blaze file
    save_path = './outputs/foraidan/'
    gbt = CalcThroughput(x, '../HISPEC_allsubs.xlsx',data_path='./inputs/')
    
    # define sections of instrument to include
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI BLUE', 
                'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
    label    = 'BSPEC_endTOend_NGS'
    throughput = gbt.run(atc_keys,save_path=save_path,label=label)
    gbt.plotTotalThroughput(label=label,save_path=save_path)
    gbt.plotSubsections(keys=atc_keys,label=label + ' Subsections',save_path=save_path)
    gbt.plotSubsectionComponents('BSPEC',save_path=save_path)

    # calc total hispec  rspec
    atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI RED', 
                'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
    label    = 'RSPEC_endTOend_NGS'
    throughput = gbt.run(atc_keys,save_path=save_path,label=label)
    gbt.plotTotalThroughput(label=label,save_path=save_path)
    gbt.plotSubsections(keys=atc_keys,label=label + ' Subsections',save_path=save_path)
    gbt.plotSubsectionComponents('RSPEC',save_path=save_path)

if __name__=='__main__':	
	#'TELESCOPE', 'AO', 'FEI  COMMON', 'FEI ATC', 'FEI BLUE', 'FEI RED', 'COUPLING', 'FIBER TRANSMISSION BLUE', 'FIBER TRANSMISSION RED', 'BSPEC ', 'RSPEC '
	configs = {}
	#configs['bspec'] = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI BLUE', 'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	#configs['rspec'] = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI RED', 'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
	#configs['Tele_to_ATC']   = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']

	# CAL paths -
	#configs['FEI_Rinject'] = ['FEI COMMON', 'FEI RED', 'COUPLING PERFECT KECK', 'FIBER TRANSMISSION RED', 'RSPEC']
	#configs['FEI_Binject'] = ['FEI COMMON', 'FEI BLUE', 'COUPLING PERFECT KECK', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	#configs['AO_Rinject']  = ['AO','FEI COMMON', 'FEI RED', 'COUPLING NGS', 'FIBER TRANSMISSION RED', 'RSPEC']
	#configs['AO_Binject']  = ['AO','FEI COMMON', 'FEI BLUE', 'COUPLING NGS', 'FIBER TRANSMISSION BLUE', 'BSPEC']
	configs['ATC_FEI']   = ['FEI COMMON', 'FEI ATC']
	configs['FEI_Ronly'] = ['FEI COMMON', 'FEI RED']
	configs['FEI_Bonly'] = ['FEI COMMON', 'FEI BLUE']

	# TODO add back injection option
	
	# combine subsystems to get full transmission and plot
	for path in configs.keys(): #['bspec']:
		label = path + '_' + tracking_band
		throughput = ct.run(configs[path],save_path=save_path,label=label)
		ax = ct.plotSubsections(configs[path],save_path=None,label=label)
		ct.plotTotalThroughput(label=label,ax=ax,save_path=save_path)

	# can also plot the components of a subsection like this:
	#ct.plotSubsectionComponents('FEI COMMON')

	plt.show()

	







	