import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout, QLabel, QSpinBox, QDoubleSpinBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QTimer
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import serial
from struct import *
import numpy as np
import time

startTime = time.time()
port = 'COM6'  # You will need to change this

############################################################################
#                        GUI Example, uses PyQt framework                  #
#                            See state example first                       #
############################################################################

###### Define amplifier class to unpack data buffer, includes waveforms
class AmpliferState:
    def __init__(self, data):
        self.enabled = bool(data[0])
        self.phaseTracking = bool(data[1])
        self.currentTracking = bool(data[2])
        self.powerTracking = bool(data[3])
        self.errorAmp = bool(data[4])
        self.errorLoad = bool(data[5])
        self.errorTemperature = bool(data[6]) 
        self.voltage = float(unpack('f', data[8:12])[0])
        self.frequency = float(unpack('f', data[12:16])[0]) 
        self.minFrequency = float(unpack('f', data[16:20])[0]) 
        self.maxFrequency = float(unpack('f', data[20:24])[0])
        self.phaseSetpoint = float(unpack('f', data[24:28])[0])
        self.phaseControlGain = float(unpack('f', data[28:32])[0])
        self.currentSetpoint = float(unpack('f', data[32:36])[0])
        self.currentControlGain = float(unpack('f', data[36:40])[0]) 
        self.powerSetpoint = float(unpack('f', data[40:44])[0])
        self.powerControlGain = float(unpack('f', data[44:48])[0])
        self.maxLoadPower = float(unpack('f', data[48:52])[0])
        self.ampliferPower = float(unpack('f', data[52:56])[0])
        self.loadPower = float(unpack('f', data[56:60])[0])
        self.temperature = float(unpack('f', data[60:64])[0])
        self.measuredPhase = float(unpack('f', data[64:68])[0])
        self.measuredCurrent = float(unpack('f', data[68:72])[0])
        self.Impedance = float(unpack('f', data[72:76])[0])
        self.transformerTruns = float(unpack('f', data[76:80])[0])
        self.voltageWave = []
        for i in range(0,250):
            self.voltageWave.append(float(unpack('f',data[80+(i*4):84+(i*4)])[0]))
        self.currentWave = []
        for i in range(250,500):
            self.currentWave.append(float(unpack('f',data[80+(i*4):84+(i*4)])[0]))
        self.voltage = self.voltage*self.transformerTruns

class App(QDialog):

    def __init__(self, argv):
        super().__init__()
        self.title = 'PDus210 - RS485 Example'
        self.left = 100
        self.top = 100
        self.width = 1800
        self.height = 800
        self.commands = []
        self.initUI()
        self.time = np.linspace(0, 47.8, 250) #Time array for waveform # TO-DO
        self.ser = serial.Serial(port=port, baudrate=460800, timeout=20) #Setup serial
        self.frequency = [0]
        self.phase = [0]
        self.time2 = [0]
        self.numberOfSamples = 1000
        self.reconnect = True
        print(argv)
        
    def initUI(self): #Setup GUI
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.createGridLayout()
        
        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
        self.setLayout(windowLayout)
        
        self.show()
        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)

        #start timer for getState
        self.timer = QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.getState)
        self.timer.start()
       
    def getState(self): #Update GUI with new amplifer state 
        global startTime
        if self.reconnect:
            self.reconnect = False
            # Disable error reports, will monitor errors from amplifier state
            self.addCommand('disERROR', '')
        error = False
        # Send commands in command list
        if(len(self.commands)>0):
            try:
                for command in self.commands:
                    self.ser.write((command + '\r').encode())
                    returned = self.ser.read_until('\r'.encode())
                    self.ser.flushInput()
                self.commands = []
            except:
                print('ERROR')
                error = True
                self.reconnect = True
                self.errorValue.setText('Communication')
                self.ser.flushInput()
        try: #Update amplifer state and GUI
            self.ser.write('getSTATEWAVE\r'.encode())
            returned = self.ser.read(2080)
            self.ser.flushInput()
            self.amp = AmpliferState(returned)

            self.updateWaveform()

            #### Monitor for errors 
            if self.amp.errorLoad:
                error = True
                self.errorValue.setText('Load Overload')

            if self.amp.errorAmp:
                error = True
                self.errorValue.setText('Amplifer Overload')
            
            if self.amp.errorTemperature:
                error = True
                self.errorValue.setText('Temperature Overload')
            endTime = time.time()
            print("time_cost =", endTime - startTime)
            startTime = endTime

        except Exception as e:
            print(e)
            error = True
            self.reconnect = True
            self.ser.flushInput()

    def addCommand(self, command, value): #Function to add commands to comand list
        if (value == ''):
            self.commands.append(command)
        else:
            self.commands.append(command+str(int(value)))
        
    def updateWaveform(self): #Updates graphs
        self.p1.clear()
        self.p1.plot(self.time, self.amp.voltageWave)
        self.p2.clear()
        self.p2.addItem(pg.PlotCurveItem(self.time, self.amp.currentWave, pen='b'))
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)   
        self.freqValue.setText(str("%.2f" % self.amp.frequency))
    
    def createGridLayout(self): #Build GUI
        self.horizontalGroupBox = QGroupBox("Grid")
        layout = QGridLayout()

        #WaveformGraph
        self.graphWidgetWaveform = pg.PlotWidget()
        self.p1 = self.graphWidgetWaveform.plotItem
        self.p1.setLabels(left = 'Voltage') 
        voltage = [0]
        time = [0]
        self.p1.plot(voltage, time)
        
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Current',color='#0000ff')
        self.p2line = self.p2.addItem(pg.PlotCurveItem([10,20,40,80,40,20], pen='b'))
        self.graphWidgetWaveform.setBackground('w')
        layout.addWidget(self.graphWidgetWaveform, 0,4,12,100)
        

       #Enable
        #Define widgets
        #Define widgets
        self.pauseLabel = QLabel('Pause:')
        self.pauseValue = QLabel('False')
        self.enablePauseButton = QPushButton('Pause')
        self.disablePauseButton = QPushButton('Resume')
        self.enablePauseButton.clicked.connect(lambda:self.pause())
        self.disablePauseButton.clicked.connect(lambda:self.resume())
        #Add widgets to grid
        layout.addWidget(self.pauseLabel, 0,0)
        layout.addWidget(self.pauseValue, 0,1)
        layout.addWidget(self.enablePauseButton, 0,2)
        layout.addWidget(self.disablePauseButton, 0,3)

        self.freqLabel = QLabel('Frequency:')
        self.freqValue = QLabel('')
        #Add widgets to grid
        layout.addWidget(self.freqLabel, 1,0)
        layout.addWidget(self.freqValue, 1,1)

        self.horizontalGroupBox.setLayout(layout)

    def updateViews(self):
        ## view has resized; update auxiliary views to match
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def pause(self):
        if self.timer.isActive():
            self.pauseValue.setText('True')
            self.timer.stop()
    def resume(self):
        if not self.timer.isActive():
            self.pauseValue.setText('False')
            self.timer.start()
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App(sys.argv)
    sys.exit(app.exec_())

