# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 17:11:20 2017

@author: pi
"""

import spidev
import time

class ad5174:
        def __init__(self, spi_channel=1):
                #establish connection
                self.spi_channel = spi_channel
                self.conn = spidev.SpiDev(0, spi_channel)
                self.conn.max_speed_hz = 1000000 # 1MHz
                
                #make register writable
                self.write(0b0001110000000011)                
                
                
        def __del__( self ):
                self.close

        def close(self):
            """
            close the spi connection opened in __init__
            """
            if self.conn != None:
                    self.conn.close
                    self.conn = None

        def bitstring(self, n):
            """
            gives back a 8 bit bit string from the number n (n need to be a max 8 bit number)
            """
            s = bin(n)[2:]
            return '0'*(8-len(s)) + s

        def write(self,cmd):
            """
            write a 16 bit command word to the ad5174
            """
            #seperate the first 8 bit 
            msb = cmd >> 8
            #seperate the second 8 bit
            lsb = cmd & 0xFF
            return self.conn.xfer2([msb,lsb])
            

            
  

#test stuff          
if __name__=="__main__":            
    ad5174().write(0b0001110000000011)
    #print(AD5174().write(0b0000010000000000))
    for r in range(1023):
        print(ad5174().write(1024+r))
        time.sleep(0.05)
    #AD5174().write(1024+1023)
    #print(AD5174().write(0b0000100000000000))
    
                
    #print(AD5174().write(0x1c03))
    #print(AD5174().write(0x0500))