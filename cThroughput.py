# Loads throughput excel sheet and
# multiplies things out to get the total
# throughput

#########################################################
# NOTES ON EXCEL INPUT FORMAT
#
# - automatically imports the first sheet
# - First column should have 1s in rows for what 
#   one wants to include
# - Section labels start with "FALSE, Note, NAME_OF_SECTION"
# - Throughput will be computed for sections as well 
#   as the total
# - Under 'Type' options are 'Coating', 'Constant', or 
#   'Internal Transmission'
#   - 'Coating' loads a file as is
#   - 'Constant' assumes the constant value in the 'value'
#      column
#   - 'Internal Transmission' uses value entry as optic 
#      thickness in mm and loads a file that has wavelength,
#      transmission, and thickness in mm as the columns.
#      The code then scales the values to the thickness value
#########################################################
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import csv,os
from scipy import interpolate
from matplotlib.ticker import MultipleLocator

import matplotlib
font = {'size'   : 14}
matplotlib.rc('font', **font)

yJ = [980,1327]
HK = [1490,2460]

###### NEW CLASS WHO DIS
class CalcThroughput():
    """
    Uses Excel throughput tracker for loading throughput for hispec and modhis options

    """
    def __init__(self,wave,excel_file, data_path='./data/throughput/hispec_subsystems/'):  
        """    
        inputs
        ------
        wave - array [nm]
            wavelength array to interpolate everything on
        excel_file - str
            name of the excel file. Assumes location is data_path
        data_path - str
            path to excel_file and the throughput coatings data that are pointed to in the excel_file

        outputs
        -------
        s - array
            base throughput (no coupling) sampled at wave
        data - dictionary
            contains individual surface data
        """
        self.wave = wave
        self.excel_file = excel_file
        self.data_path = data_path
        
        # load dictionary of transmission data for each subsection then combine
        self.transmission_dic = self._loadTransmissionData(wave,excel_file,data_path)
        
		#you can then call runThroughputCalc with the set of keys to compute throughput for
        
    def run(self,keys,save_path=None,label='test'):
        """Combine various sections into the throughputs we want 
        that are already loaded in __init__ into transmission_dic
        
        input
        ------
        keys - list
            list of keys that to include in the tranmission calculation
            e.g. for atc throughput you would do 
            		keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']
        save_path - str (default: None)
			path to where to save data, if none will not save data
        label - str (default: test)
			label to add to the saved data name

        output
        ------
        final_throughput - array
	        final throughput array sampled on wave grid. 
            Also stored as self.total_throughput
        """
        self.total_throughput = self._combineTransmission(self.wave,
                                                           self.transmission_dic, 
                                                           keys)
        # save
        if save_path != None:   
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            np.savetxt(save_path + './transmission_total_%s.txt'%label, np.vstack((self.wave,self.total_throughput)).T,delimiter=',',header='wavelength (nm),transmission (I/F) ')

        return self.total_throughput
    
    def _loadTransmissionData(self,wave,excel_file,data_path):
        """ Load transmission data into dictionary

        inputs
        ------
        wave: arr
            wavelength grid
        excel_file : str
            path to and name of excel file to load

        outputs
        -------
        transmission : dictionary
            dictionary with keys as section headers and values as 
            transmission arrays
        """
        includes, types, values, filenames, elements = self._loadThroughputFile(data_path + excel_file)

        transmission = {}
        for i, include in enumerate(includes):
            # start a dictionary entry for new section
            if types[i] == 'Note':
                key = elements[i]
                transmission[key] = np.ones_like(wave)
            # if include (first column) is 1, include it
            if include == 1:
                # process input based on entry type and mulitply all together
                transmission[key] *= self._setInput(wave,types[i], values[i], 
                                                   filenames[i],data_path)

        return transmission

    def _combineTransmission(self, x,transmission_dic, keys):
        """for key in keys, multiply all transmission entries together."""
        t_all = np.ones_like(x)
        for key in keys:
            t_all *= transmission_dic[key]
        
        return t_all
    
    def _loadThroughputFile(self,excel_file):
        """
        read excel file and return contents 

        inputs
        ------
        excel_file : str
            path to and name of excel file to load

        outputs
        -------
        includes : array
            1 if include, 0 if not
        types : array
            'Coating', 'Constant', or 'Internal Transmission'
        values : array
            value of input
        filenames : array
            file name of input
        elements : array
            section header
        """
        # read in the efficiency excel file into a dataframe ('df')
        xl = pd.ExcelFile(excel_file)
        #xl.sheet_names
        first_sheet = xl.sheet_names[0]
        df = xl.parse(first_sheet)
        #df.head()

        # get the number of active surfaces in the excel file
        #num_active_sfcs = df['Include?'].value_counts()[1]

        includes  = df['Include?']
        types     = df['Type']
        values    = df['Value']
        filenames = df['Datafile']
        elements  = df['Element']  #maybe for plotting/grouping

        return includes, types, values, filenames, elements

    def _setInput(self,wave, tt, value, file_name, data_path):
        """
        Processes a config input as either txt or float, interpolates it to x array, text file wavelengths assumes microns or nm

        inputs
        ------
        x : array
            wavelengths in nm
        tt : str
            'Coating', 'Constant', or 'Internal Transmission'
        value : float
            value of input
        filename : str
            file name of input

        outputs
        -------
        f_interp : array
            transmission values interpolated onto x array
        """
        if tt == 'Constant' or tt=='constant':
            return value
        else:
            with open(data_path + file_name.replace('\\','/'),'r') as test:
                lines = test.readlines()
                delimiter= csv.Sniffer().sniff(lines[2]).delimiter
            
            f = pd.read_csv(data_path + file_name.replace('\\','/'),sep=delimiter,engine='python').values

            if f[:,0][0] < 100:
                f[:,0] *=1000 # convert micron to nm

            # define thickness ratio if internal transmission
            thickness_ratio = value / f[:,2][0]\
                    if tt == 'Internal Transmission'\
                    else 1.0

            if np.nanmax(f[:,1]) > 1.05:
                f_interp =  interpolate.interp1d(f[:,0], f[:,1]/100,bounds_error=False,fill_value='extrapolate')
                return f_interp(wave) ** thickness_ratio
            else:    
                f_interp =  interpolate.interp1d(f[:,0], f[:,1],bounds_error=False,fill_value='extrapolate')
                return f_interp(wave) ** thickness_ratio

    def plotTotalThroughput(self,label='test',ax=None,save_path=None):
        """Plot self.total_throughput
        inputs
        -----
        label - str
			name to label the plot
        save_path - str (default None)
			path to save the plot image and the total throughput arrays 
        """
        if ax==None:    fig, ax = plt.subplots(1, 1, figsize=(9,4))
        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)

        #ax.text(385.1,0.041,'Requirement',fontsize=9)

        ax.plot(self.wave,self.total_throughput,'k',label='Total Throughput')
        ax.legend()
        #ax.set_ylim(0,np.max(self.total_throughput) * 1.1)

        # grids!
        ax.yaxis.grid(True, which='both',alpha=0.5)
        ax.yaxis.set_minor_locator(MultipleLocator(0.01))
        ax.yaxis.set_major_locator(MultipleLocator(0.1))

        ax.set_xlabel('Wavelength (nm)',fontsize=12)
        ax.set_ylabel('Throughput',fontsize=12)
        ax.grid()
        
        plt.title(label)
        
        if save_path != None:
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            plt.savefig(save_path + '/transmission_total_%s.png'%label,dpi=500)

    def plotSubsectionComponents(self,key_name):
        """
        plot subsystem components labeled by key
        
        Could be rewritten to avoid duplicate loading of excel file..
        """
        includes, types, values, filenames, elements = self._loadThroughputFile(self.data_path + self.excel_file)

        total = np.ones_like(self.wave)

        fig, ax = plt.subplots(1, 1, figsize=(8,5))
        for i, include in enumerate(includes):
            # start a dictionary entry for new section
            if types[i] == 'Note':
                key = elements[i]
            if key==key_name:
                if include == 1:
                    t = self._setInput(self.wave,types[i], values[i], filenames[i],self.data_path)
                    if types[i]=='Coating' or types[i]=='coating':
                        ax.plot(self.wave,t,label=elements[i])
                    if types[i]=='Constant' or types[i]=='constant':
                        ax.plot(self.wave,self.wave*0+t,label=elements[i])
                    total*=t

        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.1,zorder=-100)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.1)
        ax.set_xlabel('Wavelength [nm]')
        ax.set_ylabel('Transmission')
        
        ax.plot(self.wave,total,'k',lw=2)
        plt.legend(fontsize=8)
        plt.grid()

    def plotSubsections(self,keys,ax=None,save_path=None,label='test'):
        """ plot transmission for each subsystem
        
        inputs
        -----
        keys - list
            list of subsystem keywords to include in the plot e.g. 'AO' or 'FEI COMMON'
         """
        # define specific things
        if ax==None: fig, ax = plt.subplots(1, 1, figsize=(9,4))

        for k in keys: 
            # only plot if not ones
            if np.any(self.transmission_dic[k]!=1): 
                ax.plot(self.wave,self.transmission_dic[k],label=k) 

        ax.fill_between(yJ,y1=0,y2=1,facecolor='blue',alpha=0.3)
        ax.fill_between(HK,y1=0,y2=1,facecolor='red',alpha=0.3)
        ax.set_ylim(0,1.1)

        ax.set_xlabel('Wavelength (nm)',fontsize=12)
        ax.set_ylabel('Throughput',fontsize=12)
        plt.title(label)
        
        ax.legend(fontsize=7)
        ax.grid()

        if save_path != None:   
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            np.savetxt(save_path + './transmission_%s.png'%label, np.vstack((self.wave,self.total_throughput)).T,delimiter=',',header='wavelength (nm),transmission (I/F) ')

        return ax


def calc_strehl(wfe,wavelength):
    """
    Extended extended Marechal equation - used function by code
    as of No 20th. See KOAN doc for info

    inputs
    ------
    wfe: nm
    wavelength: nm, grid or single number

    outputs
    -------
    strehl at wavelength
    """
    marechal = 2*np.pi*wfe/wavelength
    strehl = np.exp(-(0.75 * (marechal + 0.2615))**2 + 0.05)

    return strehl



if __name__=='__main__':
    # example save strehl
	wfe = 120 # nm
	strehl = calc_strehl(wfe,x)
	np.savetxt('inputs/fiber/strehl_howfe_%snm.csv'%wfe, np.vstack((x,strehl)).T,delimiter=',',header='wavelength(nm), strehl')

	# example calc throughput usage
	gbt = CalcThroughput(x, '../HISPEC_allsubs.xlsx',data_path='./inputs/')
	atc_keys = ['TELESCOPE', 'AO', 'FEI COMMON', 'FEI ATC']
	throughput = gbt.run(atc_keys)
	gbt.plotTotalThroughput()
	gbt.plotSubsections(keys=atc_keys)
	gbt.plotSubsectionComponents('AO')
