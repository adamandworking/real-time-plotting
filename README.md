# Introduction

This is the repository for real-time plotting with a microcontroller or PDUS210 through Serial. The refreshing rate is around 10 frames/sec.
# Folder
## Arduino
For merging the code with your Audio-to-Digital Converter (ADC), please edit the code in the "receiveData" function. If you cannot upload the code to the microcontroller, please check if you are using Teensyduino. If no, please install that plug-in for Arduino and select the right board in the Teensyduino software.

## Python
There are 3 python source code files. Here is the table for the explanation:
|          | RS485_pyqt_piezoDrive.py                                                                                                                                                                              | RS485_pyqt_piezoDrive_lite.py                                                                                                                                                                                                                                                     | MCU_pyqt_Arduino.py                                                                                                                                                                          |
|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Usage    | This is from the template given by PiezoDrive ([link](https://github.com/PiezoDrive/RS485-API)) . I have added a pause button.                                                                            | This is the lite version of RS485_pyqt_piezoDrive.py. As there are some many features that you may not need, I have kept it as simple as I can (Just a pause button, frequency viewer and a voltage, current vs time graph). The refreshing performance has increased around 15%. | As we may want to simulate a PiezoDrive software, I have implemented a real-time graph plotting in Python. It receives the data from the microcontroller and plots it in a stable frequency. |
| Reminder | Connect the PiezoDrive with RS485 and remember to switch on the PiezoDrive. If it does not work, please check the buad rate both in the python code and PiezoDrive software whether they are the same | Connect the PiezoDrive with RS485 and remember to switch on the PiezoDrive. If it does not work, please check the buad rate both in the python code and PiezoDrive software whether they are the same                                                                             | Connect to the microcontroller with the USB-Serial port. If it does not work, please press the reboot button on the microcontroller.                                                         |


It is worth noting that the time_set has been hardcoded since I cannot estimate the spped of the ADC reading the data. You may need to find out the time cost of your ADC reading per voltage and current value, and then replace that value (located in the constructor of the Class App, the attribute called "time")  

If you want to compile the code, for Arduino, please upload it by Arduino with the Teensy plug-in. For Python, please type the command

```bash
cd Python/  # go to the directory where stores the python source code
python MCU_pyqt_Arduino.py # You can compile another source code file based on which data you are looking for
```