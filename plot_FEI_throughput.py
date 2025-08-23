# Loads throughput excel sheet and
# multiplies things out to get the total
# throughput
# last updated aug 14th, 2025

import matplotlib.pylab as plt
import numpy as np
from scipy import interpolate
from matplotlib.ticker import MultipleLocator

from utils import * 

datapath   = './inputs/'
outpath    = './outputs/'

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

# Define yJHK band passes for plotting
x = np.arange(950, 2550, 0.05)
yJ = [980,1327]
HK = [1490,2460]


if __name__=='__main__':
	# load excel_file into transmission dictionary and return total throughupt t_all
	excel_file   = './HISPEC_allsubs.xlsx'

	# load the subsection specifically
	ao, ao_tot = load_subsection(x,'AO',excel_file)
	fei_com, fei_com_tot = load_subsection(x,'FEI COMMON',excel_file)
	fei_atc, fei_atc_tot = load_subsection(x,'FEI ATC',excel_file)
	fei_red, fei_red_tot = load_subsection(x,'FEI RED',excel_file)
	fei_blue, fei_blue_tot = load_subsection(x,'FEI BLUE',excel_file)

	##############
	# plot fill between regions
	fig, ax = plt.subplots(2, 1, figsize=(9,10))
	ax[0].fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
	ax[0].fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)

	# Plot Separate sections
	ax[0].plot(x,ao_tot,'orange',lw=2,ls='-',label='AO')
	ax[0].plot(x,fei_com_tot,'m',lw=2,ls='-',label='FEI COM')
	ax[0].plot(x,fei_atc_tot,'g',lw=2,ls='-',label='FEI ATC')
	ax[0].plot(x,fei_red_tot,'r',lw=2,ls='-', label='FEI RED')
	ax[0].plot(x, fei_blue_tot,'b',lw=2,ls='-',label='FEI BLUE')

	# plot totals for each path
	ax[1].plot(x, ao_tot*fei_com_tot*fei_atc_tot,'orange',lw=2,ls='-',label="AO in to ATC")
	ax[1].plot(x, ao_tot*fei_com_tot*fei_red_tot,'r',lw=2,ls='-',label="AO in to Red Focus")
	ax[1].plot(x, ao_tot*fei_com_tot*fei_blue_tot,'b',lw=2,ls='-',label="AO in to Blue Focus")
	ax[1].plot(x, fei_com_tot*fei_atc_tot,'g',lw=2,ls='-',label="FEI input to ATC")

	ax[0].legend(fontsize=10)
	ax[1].legend(fontsize=10)

	# grids!
	ax[0].yaxis.grid(True, which='both',alpha=0.5,zorder=1000)
	ax[1].yaxis.grid(True, which='both',alpha=0.5,zorder=1000)
	#ax.yaxis.set_minor_locator(MultipleLocator(0.01))
	ax[1].yaxis.set_major_locator(MultipleLocator(0.1))

	ax[1].set_xlabel('Wavelength (nm)',fontsize=12)
	ax[0].set_ylabel('Throughput',fontsize=12)
	ax[1].set_ylabel('Throughput',fontsize=12)
	ax[0].set_title('AO + FEI System Throughput')

	if not os.path.exists(outpath):
		os.makedirs(outpath)
	
	plt.savefig(outpath + '/feiao_subsystem.png',dpi=500)
	np.savetxt(outpath + './feiao_subsystem.csv', np.vstack((x/1000,ao_tot,fei_com_tot,fei_atc_tot,fei_red_tot,fei_blue_tot)).T,delimiter=',',header='wavelength (nm),ao,fei_com,fei_atc,fei_red,fei_blue')

	


	#####
	# Save for Different Dichroics ie J, H, J_H
	def load_asahi_profiles(xnew):
		"""
		these are the final ones
		#reinterpolated onto xnew
		returns jhgap, h, j, j+h in that order in transmission (0 to 1)
	
		"""
		datapath = '/Users/ashbake/Documents/Research/Projects/HISPEC/Tests/FEI_TrackingCamera/_plot_track_bands/data/'
		path = datapath + 'asahi_roundthree/'

		# Asahi dichroic  - JH gap
		filename_jhgap = 'Final transmission model(JH gap dichroic).xlsx'
		xl_jhgap = pd.ExcelFile(path + filename_jhgap)
		first_sheet = xl_jhgap.sheet_names[0]
		df_jhgap = xl_jhgap.parse(first_sheet).values.T
		f = interpolate.interp1d(df_jhgap[0][::-1],df_jhgap[1][::-1],bounds_error=False,fill_value=-1)
		df_jhgap = f(xnew)/100

		# Asahi dichroic  - H+JH gap
		filename_hgap = 'Final transmission model(H + JH gap dichroic).xlsx'
		xl_hgap = pd.ExcelFile(path + filename_hgap)
		first_sheet = xl_hgap.sheet_names[0]
		df_hgap = xl_hgap.parse(first_sheet).values.T
		f = interpolate.interp1d(df_hgap[0][::-1],df_hgap[1][::-1],bounds_error=False,fill_value=-1)
		df_hgap = f(xnew)/100

		# Asahi dichroic  - J+JH gap
		filename_jgap = 'Final transmission model(J + JH gap dichroic).xlsx'
		xl_jgap = pd.ExcelFile(path + filename_jgap)
		first_sheet = xl_jgap.sheet_names[0]
		df_jgap = xl_jgap.parse(first_sheet).values.T
		f = interpolate.interp1d(df_jgap[0][::-1],df_jgap[1][::-1],bounds_error=False,fill_value=-1)
		df_jgap = f(xnew)/100

		# Asahi dichroic  - J+H gap
		filename_jh = 'Final transmission model(J + H dichroic).xlsx'
		xl_jh = pd.ExcelFile(path + filename_jh)
		first_sheet = xl_jh.sheet_names[0]
		df_jh = xl_jh.parse(first_sheet).values.T
		f = interpolate.interp1d(df_jh[0][::-1],df_jh[1][::-1],bounds_error=False,fill_value=-1)
		df_jh = f(xnew)/100

		return df_jhgap, df_hgap, df_jgap, df_jh

	df_jhgap, df_hgap, df_jgap, df_jh  = load_asahi_profiles(x) # index 0 is wavelength, 1 is the transmission in %

	# Recreate FEI ATC and FEI RED/BLUE paths by taking out jh gap and multiplying by new curve
	atc_h      = fei_atc_tot / (1-df_jhgap) * (1-df_hgap)
	atc_j      = fei_atc_tot / (1-df_jhgap) * (1-df_jgap)
	atc_jh     = fei_atc_tot / (1-df_jhgap) * (1-df_jh)
	feired_h   = fei_red_tot / df_jhgap * df_hgap
	feired_j   = fei_red_tot / df_jhgap * df_jgap
	feired_jh  = fei_red_tot / df_jhgap * df_jh
	feiblue_h  = fei_blue_tot/ df_jhgap * df_hgap
	feiblue_j  = fei_blue_tot/ df_jhgap * df_jgap
	feiblue_jh = fei_blue_tot/ df_jhgap * df_jh

	np.savetxt(outpath + './feiao_subsystem_jhgap.csv', np.vstack((x/1000,ao_tot,fei_com_tot,fei_atc_tot,fei_red_tot,fei_blue_tot)).T,delimiter=',',header='wavelength (um),ao,fei_com,fei_atc,fei_red,fei_blue')
	np.savetxt(outpath + './feiao_subsystem_h.csv', np.vstack((x/1000,ao_tot,fei_com_tot,atc_h,feired_h,feiblue_h)).T,delimiter=',',header='wavelength (um),ao,fei_com,fei_atc,fei_red,fei_blue')
	np.savetxt(outpath + './feiao_subsystem_j.csv', np.vstack((x/1000,ao_tot,fei_com_tot,atc_j,feired_j,feiblue_j)).T,delimiter=',',header='wavelength (um),ao,fei_com,fei_atc,fei_red,fei_blue')
	np.savetxt(outpath + './feiao_subsystem_jh.csv', np.vstack((x/1000,ao_tot,fei_com_tot,atc_jh,feired_jh,feiblue_jh)).T,delimiter=',',header='wavelength (um),ao,fei_com,fei_atc,fei_red,fei_blue')
	

	# save each path for jeb
	atc_only_jhgap    = fei_com_tot*fei_atc_tot
	atc_only_j        = fei_com_tot*atc_j
	atc_only_h        = fei_com_tot*atc_h
	atc_only_jh       = fei_com_tot*atc_jh

	feiblue_jhgap    = fei_com_tot*fei_blue_tot
	feiblue_j        = fei_com_tot*feiblue_j
	feiblue_h        = fei_com_tot*feiblue_h
	feiblue_jh       = fei_com_tot*feiblue_jh

	feired_jhgap    = fei_com_tot*fei_red_tot
	feired_j        = fei_com_tot*feired_j
	feired_h        = fei_com_tot*feired_h
	feired_jh       = fei_com_tot*feired_jh

	np.savetxt(outpath + './feiao_path_total_throughputs.csv', np.vstack((np.array(x/1000),atc_only_jhgap, atc_only_j, atc_only_h, atc_only_jh,\
																	     feiblue_jhgap, feiblue_j, feiblue_h, feiblue_jh,\
																	     feired_jhgap, feired_j, feired_h, feired_jh)).T,delimiter=',',\
																	     header='wavelength(um), feiatc_jhgap, feiatc_j, feiatc_h, feiatc_jh,' \
																		 'feiblue_jhgap, feiblue_j, feiblue_h, feiblue_jh,' \
																		 'feired_jhgap, feired_j, feired_h, feired_jh')
	
	# note that i combined these csv files into an excel file to put on sharepoint in the FEI calbiration folder 8/14/25