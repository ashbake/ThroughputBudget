# Overview

This repo contains all files and code to compute the HISPEC throughput curves

The inputs/ folder contains all the text files with info on coatings, transmissions, etc for the computation
The Excel file 'HISPEC_allsub.xlsx' contains the latest surface to surface prescription for HISPEC's optical path
The 'gary' Excel version is Gary's throughput prescription which is now outdated but kept as a comparison to the original work he has done. 

Currently emissivities have not been carried into this and Gary's work is being used for this in specsim/

cThroughput.py contains functions that can be used to read the Excel file of choice. See calc_throughput.py for how I utilize them to compute the throughput of different optical paths in HISPEC.  
