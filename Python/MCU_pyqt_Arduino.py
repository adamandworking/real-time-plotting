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

class AmpliferState:
    def __init__(self, voltage_set, current_set, freq, length, voltage_max_idx, current_max_idx):
        self.frequency = freq
        self.voltageWave = voltage_set
        self.currentWave = current_set
        self.length = length
        self.voltage_max_idx = voltage_max_idx
        self.current_max_idx = current_max_idx



startTime = time.time()
port = 'COM5'  # You will need to change this
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
        self.time = np.linspace(0, 47.8, 360) #Time array for waveform # TO-DO
        self.ser = serial.Serial(port=port, baudrate=115200, timeout=20) #Setup serial
        self.frequency = [0]
        self.phase = [0]
        self.time2 = [0]
        self.numberOfSamples = 1000
        self.reconnect = True
        
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
                self.ser.flushInput()
        try: #Update amplifer state and GUI
            self.ser.write('getSTATEWAVE\r'.encode())
            raw_freq = self.ser.read_until('\n'.encode())
            raw_length = self.ser.read_until('\n'.encode())
            voltage = self.ser.read_until('\n'.encode())
            current = self.ser.read_until('\n'.encode())
            freq = float(raw_freq.decode().replace('\n', '').replace('\r', ''))
            length = int(raw_length.decode().replace('\n', '').replace('\r', ''))
            voltage_set = self.parse_data(voltage)
            current_set = self.parse_data(current)
            voltage_max_idx = np.argmax(voltage_set)
            current_max_idx = np.argmax(current_set)
            if abs(voltage_max_idx - current_max_idx) < 5:
                print("acceptable phase shift occurs at", freq, "frequency (Hz)")
            self.amp = AmpliferState(voltage_set, current_set, freq, length, voltage_max_idx, current_max_idx)
            self.ser.flushInput()

            self.updateWaveform()
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
 
    def parse_data(self, string):
        string = string.decode()
        string = string.replace('\n', '')
        string = string.replace('\r', '')
        set_of_data = string.split(',')
        set_of_data = np.array(set_of_data)
        set_of_data = set_of_data.astype(float)
        return set_of_data

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App(sys.argv)
    sys.exit(app.exec_())

