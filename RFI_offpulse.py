"""
Interactive RFI masker using the filterbank file, and outputs the masked array that can be read into other python scripts. Also does the bandpass correction using filterbank_to_arr.
Kenzie Nimmo 2020
"""

import numpy as np
import matplotlib.pyplot as plt
import filterbank_to_arr
from pylab import *
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import filterbank
import pickle
import os
import re
import sys

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

class offpulse(object):
    def __init__(self,filename,gs):
        self.begin_times=[]
        self.end_times=[]
        self.lines={}

        ax1 = plt.subplot(gs[2]) #dynamic spectrum
        ax2 = plt.subplot(gs[0],sharex=ax1) #profile
        ax3 = plt.subplot(gs[-1],sharey=ax1) #spectrum
        self.ds = ax1
        self.spec = ax3

        self.axes = ax2 # off pulse only necessary for the profile which is in subplot ax2

        self.canvas = ax2.figure.canvas
        fil=filterbank.filterbank(filename)
        arr = filterbank_to_arr.filterbank_to_np(filename,None,bandpass=False)

        profile=np.mean(arr,axis=0)

        self.ax2plot, = ax2.plot(profile, 'k-',alpha=1.0,zorder=1)
        ax2.tick_params(axis='y', which='both', left='off', right='off', labelleft='off')
        ax2.tick_params(axis='x', labelbottom='off', top='off')
        y_range = profile.max() - profile.min()
        ax2.set_ylim(profile.min()-y_range*0.1, profile.max()*1.1)
        ax2.tick_params(labelbottom=False, labeltop=False, labelleft=False, labelright=False, bottom=True, top=True, left=True, right=True)

        fig.add_subplot(ax2)

        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)
        self.crel = self.canvas.mpl_connect('button_release_event', self.onrel)
        self.keyPress = self.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.keyRelease = self.canvas.mpl_connect('key_release_event', self.onKeyRelease)

        self.data=self.ax2plot.get_data()
        self.profile = self.data[1]
        self.x=False

    def clear_line(self,x):
        self.lines.pop(x).remove()

    def onKeyPress(self, event):
        if event.key == 'x':
            self.x = True
        if event.key == 'y':
            if self.lines['burst']:
                self.clear_line('burst')
                plt.draw()

    def onKeyRelease(self, event):
        if event.key == 'x':
            self.x = False


    def onpress(self, event):
        #if self.ctrlKey == True and self.shiftKey == True:
        if self.x == True:
            tb = get_current_fig_manager().toolbar
            if tb.mode == '':
                x1= event.xdata
                index1=np.int(x1)
                self.begin_times.append(index1)
        if self.x == False:
            return

    def onrel(self, event):
        #if self.ctrlKey == True and self.shiftKey == True:
        if self.x == True:
            tb = get_current_fig_manager().toolbar
            if tb.mode == '':
                x2= event.xdata
                index2=np.int(x2)
                self.end_times.append(index2)
                y_range = self.profile.max() - self.profile.min()
                ymin=self.profile.min()-y_range*0.1
                if self.begin_times[-1] < index2:
                    self.lines['burst'] = self.axes.hlines(y=ymin, xmin=self.begin_times[-1], xmax=index2, lw=10, color='#FF00FF',zorder=0.8)
                else:
                    self.lines['burst'] = self.axes.hlines(y=ymin, xmin=index2, xmax=self.begin_times[-1], lw=10, color='#FF00FF',zorder=0.8)
                plt.draw()
            if self.x == False:
                return



class RFI(object):
    def __init__(self,filename,gs,prof,ds,spec,ithres,ax2):
        self.begin_chan = []
        self.mask_chan = []
        self.axes = ds # off pulse only necessary for the profile which is in subplot ax2
        self.canvas = ds.figure.canvas
        self.ithres = ithres

        fil=filterbank.filterbank(filename)
        self.total_N=fil.number_of_samples
        arr = filterbank_to_arr.filterbank_to_np(filename,None)
        spectrum=np.mean(arr,axis=1)
        self.freqbins=np.arange(0,arr.shape[0],1)
        self.freqs=fil.frequencies
        threshold=np.amax(arr)-(np.abs(np.amax(arr)-np.amin(arr))*0.99)

        self.cmap = mpl.cm.binary
        self.ax1 = ds
        self.ax3 = spec
        self.ax2 = ax2
        self.ax2plot = prof
        self.ax1plot = self.ax1.imshow(arr,aspect='auto',vmin=np.amin(arr),vmax=threshold,cmap=self.cmap,origin='lower',interpolation='nearest',picker=True)
        self.cmap.set_over(color='pink')
        self.cmap.set_bad(color='red')
        self.ax1.set_xlim(0,self.total_N)
        self.ax3plot, = self.ax3.plot(spectrum, self.freqbins, 'k-',zorder=2)
        self.ax3.tick_params(axis='x', which='both', top='off', bottom='off', labelbottom='off')
        self.ax3.tick_params(axis='y', labelleft='off')
        self.ax3.set_ylim(self.freqbins[0], self.freqbins[-1])
        x_range = spectrum.max() - spectrum.min()
        self.ax3.set_xlim(-x_range/4., x_range*6./5.)

        fig.add_subplot(self.ax1)
        fig.add_subplot(self.ax3)

        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)
        self.crel = self.canvas.mpl_connect('button_release_event', self.onrel)
        self.keyPress = self.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.keyRelease = self.canvas.mpl_connect('key_release_event', self.onKeyRelease)
        self.x = False


    def onKeyPress(self, event):
        if event.key == 'x':
            self.x = True


    def onKeyRelease(self, event):
        if event.key == 'x':
            self.x = False
        #if event.key == 'y':
        #    self.y = False


    def onpress(self, event):
        #if self.ctrlKey == True and self.shiftKey == True:
        if self.x == True:
            return
        if self.x == False:
            tb = get_current_fig_manager().toolbar
            if tb.mode == '':
                y1= event.ydata
                arr=self.ax1plot.get_array()
                vmin = np.amin(arr)
                index=find_nearest(self.freqbins,y1)
                self.begin_chan.append(index)

        """
        if self.y == True:
            tb = get_current_fig_manager().toolbar
            if tb.mode == '':
                y_range = self.profile.max() - self.profile.min()
                ymin=self.profile.min()-y_range*0.1
                if begin_times[-1] < end_times[-1]:
                    ax.hlines(y=ymin, xmin=begin_times[-1], xmax=end_times[-1], lw=10, color='#FFFFFF',zorder=1.0)
                else:
                    ax.hlines(y=ymin, xmin=end_times[-1], xmax=begin_times[-1], lw=10, color='#FFFFFF',zorder=1.0)
        """

    def onrel(self, event):
        #if self.ctrlKey == True and self.shiftKey == True:
        if self.x == True:
            return
        if self.x == False:
            tb = get_current_fig_manager().toolbar
            if tb.mode == '':
                y2= event.ydata
                arr=self.ax1plot.get_array()
                vmin = np.amin(arr)
                index2=find_nearest(self.freqbins,y2)
                if self.begin_chan[-1] > index2:
                    arr[index2:self.begin_chan[-1],:]=vmin-100
                else:
                    arr[self.begin_chan[-1]:index2,:]=vmin-100
                mask = arr<vmin-50
                arr = np.ma.masked_where(mask==True,arr)
                self.ax1plot.set_data(arr)
                profile = np.mean(arr,axis=0)
                self.ax2plot.set_data(np.arange(0,self.total_N,1),profile)
                self.ax3plot.set_data(np.mean(arr,axis=1),self.freqbins)
                threshold=np.amax(arr)-(np.abs(np.amax(arr)-np.amin(arr))*self.ithres)
                self.ithres-=0.005
                self.ax1plot.set_clim(vmin=np.amin(arr),vmax=threshold)
                spectrum =  np.mean(arr,axis=1)
                self.ax3.set_xlim(np.amin(spectrum),np.amax(spectrum))
                y_range = profile.max() - profile.min()
                self.ax2.set_ylim(profile.min()-y_range*0.1, profile.max()*1.1)

                self.cmap.set_over(color='pink')
                plt.draw()
                if self.begin_chan[-1] > index2:
                    for i in range(len(np.arange(index2,self.begin_chan[-1],1))):
                        self.mask_chan.append(np.arange(index2,self.begin_chan[-1],1)[i])
                else:
                    for i in range(len(np.arange(self.begin_chan[-1],index2,1))):
                        self.mask_chan.append(np.arange(self.begin_chan[-1],index2,1)[i])
                
                self.final_spec = np.mean(arr,axis=1)

if __name__ == '__main__':

    rows=2
    cols=2
    path = './'
    filfile = sys.argv[1]
    filename = os.path.join(path,filfile)
    fil=filterbank.filterbank(filename)
    total_N = fil.number_of_samples
    tot_freq = fil.header['nchans']
    fig = plt.figure(figsize=(10, 10))
    gs = gridspec.GridSpec(2, 2, wspace=0., hspace=0., height_ratios=[0.5,]*(rows-1)+[2,], width_ratios=[5,]+[1,]*(cols-1))

    ithres=0.9
    #plt.connect('button_press_event', onclick)
    #plt.connect('button_release_event', lambda event: onrel(event, ithres))
    offpulse_prof = offpulse(filename,gs)
    ds = offpulse_prof.ds
    spec = offpulse_prof.spec
    prof = offpulse_prof.ax2plot
    ax2 = offpulse_prof.axes
    RFImask = RFI(filename,gs,prof,ds,spec,ithres,ax2)
    plt.show()

    begin_times = offpulse_prof.begin_times
    end_times = offpulse_prof.end_times
    if begin_times[-1]<end_times[-1]:
        off_pulse=np.append(np.arange(0,begin_times[-1],1),np.arange(end_times[-1],total_N,1))
    else:
        off_pulse=np.append(np.arange(0,end_times[-1],1),np.arange(begin_times[-1],total_N,1))

    picklename = re.search('(.*).fil',filfile).group(1)

    numchan = np.zeros_like(RFImask.mask_chan)
    numchan+=tot_freq
    mask_chans = np.abs(numchan-np.array(RFImask.mask_chan))
    
    offpulsefile = '%s_offpulse_time.pkl'%picklename
    with open(offpulsefile, 'wb') as foff:
        pickle.dump(off_pulse, foff)

    maskfile = '%s_mask.pkl'%picklename
    with open(maskfile, 'wb') as fmask:
        pickle.dump(mask_chans, fmask)


    burst = {}
    
    burst['array_corrected']=filterbank_to_arr.filterbank_to_np(filename, maskfile, bandpass=True, offpulse=offpulsefile, nbins=6) #zapped and bp corrected array
    burst['array_uncorrected']=filterbank_to_arr.filterbank_to_np(filename, None)
    burst['mask']=mask_chans
    burst['t_samp']=fil.header['tsamp']
    burst['freqs']=fil.frequencies

    with open('%s.pkl'%picklename, 'wb') as f:
        pickle.dump(burst, f)


    plt.plot(RFImask.final_spec)
    plt.show()