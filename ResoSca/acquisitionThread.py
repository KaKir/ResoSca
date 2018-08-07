# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 15:33:30 2017

@author: pi
"""
import time
import numpy as np
from PyQt4 import QtCore
from HC_SR08 import dds
from mcp3204b import MCP3208 as mcp
from scipy.optimize import curve_fit
from digipot import ad5174

class acquisition_cont(QtCore.QThread):
    
    
    updatePlotSignal = QtCore.pyqtSignal(np.ndarray, np.ndarray)    
    
    def __init__(self):
        super().__init__()
        #set empty variables for the measurement results
        self.x=np.array([])
        self.y=np.array([])
        #calibration parameters of the phase shifter
        #minimla resistance
        self.r_0 = 37.5
        #maximum resistance
        self.r_max = 10030
        #capacity of C6
        self.cap = 6.8*10**(-9)
        
    def run(self):
        """
        run this sub thread
        """
        self.x=np.array([])
        self.y=np.array([])
        self.scan(self.frequency, self.samples, self.wait_time, self.phase, self.x_range)        
        
    @QtCore.pyqtSlot(int, float, float, float, float)
    def updateVariables(self, Samples, X_Range, WaitTime, Phase, LockInFrequency):
        """
        update the variables for the measurement and the fit
        """
        self.samples = Samples
        self.wait_time = WaitTime
        self.x_range = X_Range
        self.phase = Phase
        self.frequency = LockInFrequency
#        print([self.samples,self.wait_time,self.x_range,self.phase,self.frequency],flush=True)

        
    def setPhase(self,phase,frequency):
        """
        applies a phase to the reference signal of the lock in; approximately between 175deg and 8deg at 6.8 nF (depending on the capacitator in the all-pass-filter)
        """
        #determine the wiper position of the  ad5174
        wiperPos = self.roundTraditionalInt((np.tan((np.pi-np.absolute(phase)*np.pi/180)/2)/(2*np.pi*frequency*self.cap)-self.r_0)*1023/(self.r_max-self.r_0))
        if wiperPos >=1023:
            wiperPos = 1023
        elif wiperPos <= 0:
            wiperPos = 0
        #create command to write wiper position in the ad5174 memory
        #print(wiperPos, flush = True)
        command = 1024 + wiperPos
        #write the command to the ad5174
        allpass = ad5174()
        allpass.write(command)
        allpass.close()
        
    def scan(self,frequency,samples,wait_time, phase, x_range):
        """
        run the measurement and aquire data
        """
        #set phase
        self.setPhase(phase, frequency)
        #initialise
        self.abort = False
        self.ad=mcp()
        self.osc=dds()
        self.osc.start(frequency)
        da_data=np.zeros(samples)
        #measurement loop
        t0 = time.time()
        t_update = t0
        while True:
            t0, breaker = self.measureLoop(da_data,frequency,samples,wait_time, t0, x_range)
            t_update2 = time.time()
            if t_update2 - t_update > 0.1:
                self.liveUpdater()
                t_update = time.time()
            if breaker == True:
                break
        #close connections
        self.osc.stop()
        self.ad.close()
        #fit
#        gamma = self.fwhm_fit/2
#        self.fit(self.x,self.y,self.center_frequency_fit, self.intensity_fit, gamma)
#        self.fitUpdater()
        
    def measureLoop(self,da_data,frequency,samples,wait_time, t0, x_range)    :
        """
        measurement loop for the data aquisition function
        subroutine for scan 
        to put this in a subroutine has the one and only purpose to make the measurement abortable
        abort can always trigger when the subroutine is called
        
        """
        if self.abort == False:
            time.sleep(wait_time)
            n=0
            t1 = time.time()
            while n<samples:             
                # Read the ad data
                da_data[n]=self.ad.read(0)
                n=n+1
                
            t2 = time.time()
            tm= ((t2 + t1)/2) -t0
            self.y = np.append(self.y,[np.array([(sum(da_data)/samples)-2048])])
            self.x = np.append(self.x,[np.array([tm])])
            if (tm) > x_range:   
                self.y = self.y[self.x > 0]
                self.x = self.x[self.x > 0]-(tm - x_range)
#                self.x = np.delete(self.x,0,0)
#                self.y = np.delete(self.y,0,0)
                t0 = t0 + tm - x_range

            return t0, False
        else :
            return t0, True  


    def liveUpdater(self):
        """
        updates the plot of the measured data
        """
        self.updatePlotSignal.emit(self.x[self.x != 0], self.y[self.x != 0])
#        print([self.x,self.y])
#        self.updatePlotSignal.emit(self.x, self.y)

         
    @QtCore.pyqtSlot()
    def breakIt(self):
        """
        abort the measurement
        """
        self.abort = True

    def roundTraditionalInt(self, val):
        """
        more reliable 'round' function
        """
#        print(val,flush = True)
        return int(round(val+10**(-len(str(val))-1)))











class acquisition(QtCore.QThread):
    
    updatePlotSignal = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    updateFitSignal  = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    
    def __init__(self):
        super().__init__()
        #set empty variables for the measurement results
        self.x=np.empty(0,float)
        self.y=np.empty(0,float)
        
        #calibration parameters of the phase shifter
        self.r_0 = 37.5
        self.r_max = 10030
        self.cap = 6.44*10**(-9)
               
        
    def run(self):
        """
        run this sub thread
        """
        self.updateVariables
        self.scan(self.freq_start, self.freq_stop, self.freq_step, self.samples_per_freq, self.wait_time)
        
    @QtCore.pyqtSlot(int,int, float, int, float, float, float, float, float)
    def updateVariables(self, freq_start, freq_stop, freq_step, samples, Wait_time, intensity_fit, fwhm_fit, center_frequency_fit, phase):
        """
        update the variables for the measurement and the fit
        """
        self.freq_start = freq_start
        self.freq_stop = freq_stop
        self.freq_step = freq_step
        self.samples_per_freq = samples
        self.wait_time = Wait_time
        self.intensity_fit = intensity_fit
        self.fwhm_fit = fwhm_fit
        self.center_frequency_fit = center_frequency_fit
        self.phase = phase
        
    @QtCore.pyqtSlot()
    def breakIt(self):
        """
        abort the measurement
        """
        self.abort = True
        
    def roundTraditionalInt(self, val):
        """
        more reliable 'round' function
        """
        return int(round(val+10**(-len(str(val))-1)))
            
    def setPhase(self,phase,frequency):
        """
        applies a phase to the reference signal of the lock in; approximately between 175deg and 8deg at 6.8 nF (depending on the capacitator in the all-pass-filter)
        """
        #determine the wiper position of the  ad5174
        wiperPos = self.roundTraditionalInt((np.tan((np.pi-np.absolute(phase)*np.pi/180)/2)/(2*np.pi*frequency*self.cap)-self.r_0)*1023/(self.r_max-self.r_0))
        if wiperPos >=1023:
            wiperPos = 1023
        elif wiperPos <= 0:
            wiperPos = 0
        #create command to write wiper position in the ad5174 memory
        #print(wiperPos, flush = True)
        command = 1024 + wiperPos
        #write the command to the ad5174
        allpass = ad5174()
        allpass.write(command)
        allpass.close()
        
    
    def difLorentzian(self,x, xshift, ii, gamma, yshift):
        """
        mathematical function of a differential lorentzian or cauchy distribution
        """
        return ii*((-2*gamma**2*(x-xshift))/((x-xshift)**2+gamma**2)**2)+yshift
        
    def fit(self,xdata, ydata, xshift, ii, gamma):
        """
        fit the measured data with the differential lorentzian from difLorentzian
        """
        begin = int(len(ydata)*0.1)
        yshift= np.mean(ydata[0:begin])
        #get optimal parameters
#        self.popt, self.pcov = curve_fit(self.difLorentzian, xdata[xdata != 0], ydata[xdata != 0],method='dogbox',p0=[xshift, ii, gamma, yshift])
        try:
            self.popt, self.pcov = curve_fit(self.difLorentzian, xdata[xdata != 0], ydata[xdata != 0], method='dogbox', p0=[xshift, ii, gamma, yshift])
        except (TypeError, RuntimeError):
            print("fit failed!",flush=True)
            self.fitFailed = True
            return None
        #create fitted function
        self.fitpoints = self.difLorentzian(xdata[xdata != 0],self.popt[0],self.popt[1],self.popt[2],self.popt[3])
        self.fitFailed = False
        self.fitUpdater()
        
    
    def scan(self,freq_start,freq_stop,freq_step,samples_per_freq,wait_time):
        """
        run the measurement and aquire data
        """
        #set phase
        centerFreq = freq_start+(freq_start-freq_stop)/2
        self.setPhase(self.phase, centerFreq)
        #initialise
        self.abort = False
        self.ad=mcp()
        self.osc=dds()
        da_data=np.zeros(samples_per_freq)
        i=0
        freq=freq_start
        self.y=np.zeros((freq_stop-freq)/freq_step+1)
        self.x=np.zeros((freq_stop-freq)/freq_step+1)
        #measurement loop
        while freq<freq_stop:
            i, freq, breaker = self.measureLoop(da_data,i,freq,freq_step,samples_per_freq,wait_time)
            if breaker == True:
                break
        #close connections
        self.osc.stop()
        self.ad.close()
        #fit
        gamma = self.fwhm_fit/2
        self.fit(self.x,self.y,self.center_frequency_fit, self.intensity_fit, gamma)
        
        
    def measureLoop(self,da_data,i,freq,freq_step,samples_per_freq,wait_time)    :
        """
        measurement loop for the data aquisition function
        subroutine for scan 
        to put this in a subroutine has the one and only purpose to make the measurement abortable
        abort can always trigger when the subroutine is called
        
        """
        if self.abort == False:
            self.osc.start(freq)
            time.sleep(wait_time)
            n=0
            while n<samples_per_freq:#t<measure_time:
                
                # Read the ad data
                da_data[n]=self.ad.read(0)
                n=n+1
            #print(i,flush=True)
            #self.osc.stop()
            self.y[i]=(sum(da_data)/samples_per_freq)-2048
            self.x[i]=(freq)
            self.liveUpdater()
            #print(self.x,self.y)
            i=i+1
            freq=freq+freq_step
            
        
            return i, freq, False
        else :
            return i, freq, True
                
    def fitUpdater(self):
        """
        prints the fit in the gui graph
        """
        if self.fitFailed:
            return None
        else:
            self.updateFitSignal.emit(self.popt, self.pcov, self.x[self.x != 0], self.fitpoints)
        
    def liveUpdater(self):
        """
        updates the plot of the measured data
        """
        self.updatePlotSignal.emit(self.x[self.x != 0], self.y[self.x != 0])
    
        
    #def updater(self,plo):
    #    plo.setData(x=self.x,y=self.y) #x_data is not necessary
    #    print("Updating plot")
    #    app.processEvents()
    #    return 

    def give(self):
        """
        I don't think this is used don't  want to deleate it either
        """
        return [self.x,self.y]