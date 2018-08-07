# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 17:11:02 2017

@author: pi
"""
from PyQt4 import QtCore, QtGui#, uic
import os
#translate the QT .ui file into a python .py file with a bash script ./uitopy.sh
os.chdir("./gui")
os.system("./uitopy.sh")
os.chdir("..")

from gui.gui import Ui_MainWindow
from acquisitionThread import acquisition as actrd, acquisition_cont as actrd_cont
import csv
import numpy as np
import datetime


class setUpGui(QtCore.QObject):
    
    updateInput = QtCore.pyqtSignal(int, int, float, int)

    def __init__(self,window):
    
        super(setUpGui,self).__init__()
        self.ui = Ui_MainWindow()
        #dirname = os.path.dirname(__file__)
        #ui_filename = os.path.join(dirname, 'gui/gui02.ui')
        #self.ui = uic.loadUi(ui_filename, self)
        #self.ui.show()
        self.ui.setupUi(window)
        
        
        #define pens for the graphs
        #self.fitpen = QtGui.Qpen(brush=(173, 21, 16) , width=3.0, style=QtCore.Qt.DashLine,)     
        
        # Initialise plot
        self.uiplot = self.ui.graphicsView.plot(pen = (16, 152, 173))
        self.uiplot_con = self.ui.graphicsView_2.plot(pen = (16, 152, 173))        
        self.uifit  = self.ui.graphicsView.plot()
        #self.uifit.Qpen(brush=(173, 21, 16) , width=3.0, style=QtGui.DashLine,) 
        
        # Initialise measurement class for the resonance scan
        self.resonancescan=actrd()
        
        # Initialise measurement class for the continous scan
        self.continousscan=actrd_cont()
        
        #load default values        
        self.loadParameters()  
        self.loadParameters_cont()
        
        #live-update plot
        self.resonancescan.updatePlotSignal.connect(self.uiplot.setData)         
        self.continousscan.updatePlotSignal.connect(self.uiplot_con.setData)  
        #update fit
        self.resonancescan.updateFitSignal.connect(self.showFit)        
        
        #modify plot cont
        self.ui.graphicsView.setLabel('left','intensity',units='arb. units')
        self.ui.graphicsView.setLabel('bottom','frequency',units='Hz')
        self.ui.graphicsView_2.setLabel('left','intensity',units='arb. units')
        self.ui.graphicsView_2.setLabel('bottom','time',units='s')  
        try:
            self.xrange_cont = float(self.ui.x_range_cont.displayText())
            self.ui.graphicsView_2.setXRange(0,self.xrange_cont, padding=None, update=True)
        except ValueError:
            print("no x-range is set for the continuous meassurement")
        
#        #live-update plot
#        self.resonancescan.updatePlotSignal.connect(self.uiplot.setData)         
#        self.continousscan.updatePlotSignal.connect(self.uiplot_con.setData)  
#        #update fit
#        self.resonancescan.updateFitSignal.connect(self.showFit)                
        
        # change-textbox actions
        self.ui.start_freq.textChanged.connect(self.updateInputEmit)
        self.ui.stop_freq.textChanged.connect(self.updateInputEmit)
        self.ui.freq_step.textChanged.connect(self.updateInputEmit)
        self.ui.iterations_per_point.textChanged.connect(self.updateInputEmit)
        self.ui.wait_time.textChanged.connect(self.updateInputEmit)
        self.ui.phase.textChanged.connect(self.updateInputEmit)
        # change-textbox actions for continuous meassurement
        self.ui.x_range_cont.textChanged.connect(self.updateInputEmit_Cont)
        self.ui.measurementsperpoint_cont.textChanged.connect(self.updateInputEmit_Cont)
        self.ui.phase_cont.textChanged.connect(self.updateInputEmit_Cont)
        self.ui.wait_time_cont.textChanged.connect(self.updateInputEmit_Cont)
        self.ui.lock_in_frequency_cont.textChanged.connect(self.updateInputEmit_Cont)
        
        # Button actions
        self.ui.scan.clicked.connect(self.runScan)
        self.ui.stop.clicked.connect(self.breakScan)
        self.ui.close.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.ui.save_default.clicked.connect(self.saveParameters)
        self.ui.load_default.clicked.connect(self.loadParameters)
        self.ui.save.clicked.connect(self.file_save)
        self.ui.save_default_cont.clicked.connect(self.saveParameters_cont)
        self.ui.load_default_cont.clicked.connect(self.loadParameters_cont)
        self.ui.start_con.clicked.connect(self.runScan_con)
        self.ui.stop_con.clicked.connect(self.breakScan_con)
        self.ui.save_continous.clicked.connect(self.file_save_cont)
        
        self.updateInputEmit()
        self.updateInputEmit_Cont() 
        
      
        
   
                
        
    def updateInputEmit_Cont(self):
        try:
            self.continousscan.updateVariables(int(self.ui.measurementsperpoint_cont.displayText())
            ,float(self.ui.x_range_cont.displayText()),float(self.ui.wait_time_cont.displayText())
            ,float(self.ui.phase_cont.displayText()),float(self.ui.lock_in_frequency_cont.displayText()))
        except ValueError:
            return None
        
    def updateInputEmit(self):
        """
        updates the input variables into the measurement thread.
        """
        try:
            self.resonancescan.updateVariables(int(self.ui.start_freq.displayText())
            ,int(self.ui.stop_freq.displayText())
            ,float(self.ui.freq_step.displayText())
            ,int(self.ui.iterations_per_point.displayText())
            ,float(self.ui.wait_time.displayText())
            ,float(self.ui.intensity_fit.displayText())
            ,float(self.ui.fwhm_fit.displayText())
            ,float(self.ui.center_frequency_fit.displayText())
            ,float(self.ui.phase.displayText()))
        except ValueError:
            return None
        
    def runScan(self):
        """
        resets the plot window and the fit parameter output text boxes and 
        starts the measurement routine for the resonance scan with automatic fit at the end.
        """
        self.uifit.setData(x=[], y=[])
        self.uiplot.setData(x=[], y=[])
        self.resonancescan.start()
        self.ui.intensity.setText('')
        self.ui.qfactor.setText('')
        self.ui.fwhm.setText('')
        self.ui.center_freq.setText('')
        
    def runScan_con(self):
        """
        resets the plot window and the fit parameter output text boxes and 
        starts the measurement routine for the resonance scan with automatic fit at the end.
        """
        self.ui.graphicsView_2.setLabel('left','intensity',units='arb. units')
        self.ui.graphicsView_2.setLabel('bottom','time',units='s')  
        try:
            self.xrange_cont = float(self.ui.x_range_cont.displayText())
            self.ui.graphicsView_2.setXRange(0,self.xrange_cont, padding=None, update=True)
        except ValueError:
            print("no x-range is set for the continuous meassurement")
        
        
        self.uiplot_con.setData(x=[], y=[])
        self.continousscan.start()
        
    def breakScan(self):
        """
        stops the measurement (the program will still try to fit the data)
        """
        self.resonancescan.breakIt()
    
    def breakScan_con(self):
        """
        stops the measurement (the program will still try to fit the data)
        """
        self.continousscan.breakIt()
        
    def showFit(self, popt, pcov, xpoints, fitpoints):
        """
        draws the fit curve with the paramters from the fit routine
        """
        xshift = popt[0]
        intensity = popt[1]
        fwhm = popt[2]*2
        q_factor = xshift/fwhm
        self.ui.intensity.setText(str(intensity))
        self.ui.qfactor.setText(str(q_factor))
        self.ui.fwhm.setText(str(fwhm))
        self.ui.center_freq.setText(str(xshift))
        self.uifit.setData(x=xpoints, y=fitpoints)
        
    
                        
    def saveParameters(self):
        """
        saves the actual parameters from the resonance scan to a csv file
        """
        parameters = [int(self.ui.start_freq.displayText()),
                      int(self.ui.stop_freq.displayText()),
                      float(self.ui.freq_step.displayText()),
                      int(self.ui.iterations_per_point.displayText()),
                      float(self.ui.wait_time.displayText()),
                      float(self.ui.intensity_fit.displayText()),
                      float(self.ui.fwhm_fit.displayText()),
                      float(self.ui.center_frequency_fit.displayText()),
                      float(self.ui.phase.displayText())]
        with open('parameters.csv',"w",newline="") as f:
            writer = csv.writer(f)
            writer.writerow(parameters)
            
            
    def loadParameters(self):
        """
        load the saved parameters for the resonance scan from the parameters file if it exists
        """
        try:
            with open('parameters.csv',newline="") as f:
                reader = csv.reader(f,delimiter=',')
                parameters_read=[]
                for row in reader:
                    parameters_read.append(row)
            self.ui.start_freq.setText(parameters_read[0][0])
            self.ui.stop_freq.setText(parameters_read[0][1])
            self.ui.freq_step.setText(parameters_read[0][2])
            self.ui.iterations_per_point.setText(parameters_read[0][3])
            self.ui.wait_time.setText(parameters_read[0][4])
            self.ui.intensity_fit.setText(parameters_read[0][5])
            self.ui.fwhm_fit.setText(parameters_read[0][6])
            self.ui.center_frequency_fit.setText(parameters_read[0][7])
            self.ui.phase.setText(parameters_read[0][8])
            self.updateInputEmit()
        except IOError:
            print("no resonance scan parameter file found")
            
    def saveParameters_cont(self):
        """
        saves the actual parameters from the resonance scan to a csv file
        """
        parameters = [int(self.ui.measurementsperpoint_cont.displayText()),
                      float(self.ui.wait_time_cont.displayText()),
                      float(self.ui.x_range_cont.displayText()),
                      float(self.ui.phase_cont.displayText()),float(self.ui.lock_in_frequency_cont.displayText())]
        with open('parameters_cont.csv',"w",newline="") as f:
            writer = csv.writer(f)
            writer.writerow(parameters)
            
            
    def loadParameters_cont(self):
        """
        load the saved parameters for the resonance scan from the parameters file if it exists
        """
        try:
            with open('parameters_cont.csv',newline="") as f:
                reader = csv.reader(f,delimiter=',')
                parameters_read=[]
                for row in reader:
                    parameters_read.append(row)
            self.ui.measurementsperpoint_cont.setText(parameters_read[0][0])
            self.ui.x_range_cont.setText(parameters_read[0][2])
            self.ui.phase_cont.setText(parameters_read[0][3])
            self.ui.wait_time_cont.setText(parameters_read[0][1])
            self.ui.lock_in_frequency_cont.setText(parameters_read[0][4])
            #self.updateInputEmit_cont()
        except IOError:
            print("no continous scan parameter file found")
        
        
    def file_save(self):
        """
        saves 3 filese to the directory chosen by the dialog window of QtGui.QFileDialog.getSaveFileName
        Format is csv.
        The Filename consists of a choosen name + a prefix + the date
        File 1: Measurement Data
        File 2: Fit Data
        File 3: Fit Parameters
        
        Just saving will creating a new file when at least one minute has passed since the last save.
        """
        fullname = QtGui.QFileDialog.getSaveFileName(None, 'resosca save', "/home/pi/Desktop/Saves_Resosca/resosca.csv")
        name     = fullname.split(".")[0] 
        DATA     = np.column_stack((self.resonancescan.x[self.resonancescan.x != 0],self.resonancescan.y[self.resonancescan.x != 0]))
        date     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        savedate = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        np.savetxt(name + '_' + savedate + '_DATA.csv', DATA, delimiter=",",header=' Data \n date: ' + date + '\n x,y')
        if hasattr(self.resonancescan, "fitpoints"):
            FIT      = np.column_stack((self.resonancescan.x[self.resonancescan.x != 0],self.resonancescan.fitpoints))
            np.savetxt(name + '_' + savedate + '_FIT.csv', FIT, delimiter=",",header=' Fit \n date: ' + date + '\n x,y')
            FIT_PARAMETERS = [[self.resonancescan.popt[0],self.resonancescan.popt[1],self.resonancescan.popt[2],self.resonancescan.popt[3],self.resonancescan.popt[0]/(2*self.resonancescan.popt[2])]]
            print(FIT_PARAMETERS)
            print(type(FIT_PARAMETERS))
            np.savetxt(name + '_' + savedate + '_FITparameters.csv', FIT_PARAMETERS, delimiter=",",header=' Fit parameters \n date: ' + date + '\n center frequency, intensity, gamma (hwhm), y-offset, q-factor (center frequency/(2*gamma))')
        

    def file_save_cont(self):
        """
        saves a filese to the directory chosen by the dialog window of QtGui.QFileDialog.getSaveFileName
        Format is csv.
        The Filename consists of a choosen name + a prefix + the date
        File 1: Measurement Data
        
        Just saving will creating a new file when at least one minute has passed since the last save.
        """
        fullname = QtGui.QFileDialog.getSaveFileName(None, 'resosca save', "/home/pi/Desktop/Saves_Resosca/resosca.csv")
        name     = fullname.split(".")[0] 
        DATA     = np.column_stack((self.continousscan.x[self.continousscan.x != 0],self.continousscan.y[self.continousscan.x != 0]))
        date     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        savedate = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        np.savetxt(name + '_' + savedate + '_DATA.csv', DATA, delimiter=",",header=' Data \n date: ' + date + '\n x,y')
#        if hasattr(self.resonancescan, "fitpoints"):
#            FIT      = np.column_stack((self.resonancescan.x[self.resonancescan.x != 0],self.resonancescan.fitpoints))
#            np.savetxt(name + '_' + savedate + '_FIT.csv', FIT, delimiter=",",header=' Fit \n date: ' + date + '\n x,y')
#            FIT_PARAMETERS = [[self.resonancescan.popt[0],self.resonancescan.popt[1],self.resonancescan.popt[2],self.resonancescan.popt[3],self.resonancescan.popt[0]/(2*self.resonancescan.popt[2])]]
#            print(FIT_PARAMETERS)
#            print(type(FIT_PARAMETERS))
#            np.savetxt(name + '_' + savedate + '_FITparameters.csv', FIT_PARAMETERS, delimiter=",",header=' Fit parameters \n date: ' + date + '\n center frequency, intensity, gamma (hwhm), y-offset, q-factor (center frequency/(2*gamma))')
  

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    gui = setUpGui(win)
    
    win.show()
    sys.exit(app.exec_())