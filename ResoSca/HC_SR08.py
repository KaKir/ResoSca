# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 15:56:19 2017

@author: pi
"""

# import GPIO module
import RPi.GPIO as GPIO
class dds(object):
    def __init__(self):
               
        # setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        
        # Define GPIO pins
        self.W_CLK = 32
        self.FQ_UD = 36
        self.DATA = 38
        self.RESET = 40
        
        # setup IO bits
        GPIO.setup(self.W_CLK, GPIO.OUT)
        GPIO.setup(self.FQ_UD, GPIO.OUT)
        GPIO.setup(self.DATA, GPIO.OUT)
        GPIO.setup(self.RESET, GPIO.OUT)
        
        # initialize everything to zero
        GPIO.output(self.W_CLK, False)
        GPIO.output(self.FQ_UD, False)
        GPIO.output(self.DATA, False)
        GPIO.output(self.RESET, False)
    
    # Function to send a pulse to GPIO pin
    def pulseHigh(self,pin):
        GPIO.output(pin, True)
        GPIO.output(pin, True)
        GPIO.output(pin, False)
        return
    
    # Function to send a byte to AD9850 module
    def tfr_byte(self,data):
        for i in range (0,8):
            GPIO.output(self.DATA, data & 0x01)
            self.pulseHigh(self.W_CLK)
            data=data>>1
        return
    
    # Function to send frequency (assumes 125MHz xtal) to AD9850 module
    def sendFrequency(self,frequency):
        freq=int(frequency*(2**32/125000000))
        
        for b in range (0,4):
            self.tfr_byte(freq & 0xFF)
            freq=freq>>8
        self.tfr_byte(0x00)
        self.pulseHigh(self.FQ_UD)
        return
    
    # start the DDS module
    def start(self,freq):
         frequency = freq
         self.pulseHigh(self.RESET)
         self.pulseHigh(self.W_CLK)
         self.pulseHigh(self.FQ_UD)
         self.sendFrequency(frequency)
    
    # stop the DDS module
    def stop(self):
        self.pulseHigh(self.RESET)
    
    #cleanup pin connection
    def clean(self):
        GPIO.cleanup()
        
if __name__=="__main__":
    fre=10000.5
    dds().start(fre)
    