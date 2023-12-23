#!/usr/bin/env python3

import ntcore
from time import sleep
import subprocess
import json


class SysInfoPublisher:

    def setupNTTopics(self):
        # Get the default instance of NetworkTables that was created automatically
        # when the robot program starts
        inst = ntcore.NetworkTableInstance.getDefault()

        inst.startClient4("OrangePiSysInfo")

        inst.setServerTeam(4068)
        #inst.setServer("192.168.1.50", ntcore.NetworkTableInstance.kDefaultPort4)

        # Get the table within that instance that contains the data.
        # todo: name this with the coprocessor name ?
        table = inst.getTable("coprocessor")

        # Start publishing topics within that table that correspond to the X and Y values
        # for some operation in your program.
        # The topic names are actually "/datatable/x" and "/datatable/y".
        self.systemLoadPub = table.getDoubleTopic("system_load").publish()
        self.ipAddressPub = table.getStringTopic("ip_address").publish()
        self.memoryUsagePub = table.getDoubleTopic("memory_usage").publish()
        self.upTimePub = table.getStringTopic("up_time").publish()
        self.cpuTemperaturePub = table.getDoubleTopic("cpu_temperature").publish()

        self.systemLoad = 0
        self.ipAddress = 0
        self.memoryUsage = 0
        self.upTime = 0
        self.cpuTemperature = 0

    def publishValues(self):
        # Publish values that are constantly increasing.
        self.systemLoadPub.set(self.systemLoad)
        self.ipAddressPub.set(self.ipAddress)
        self.memoryUsagePub.set(self.memoryUsage)
        self.upTimePub.set(self.upTime)
        self.cpuTemperaturePub.set(self.cpuTemperature)
        
    def getSystemValues(self):
        result = subprocess.run(['/home/orangepi/sysinfo.sh'], stdout=subprocess.PIPE)
        values = json.loads(result.stdout.decode('utf-8'))
        print(values)
        self.systemLoad = values['SystemLoad']
        self.ipAddress = values['IP']
        self.memoryUsage = values['MemoryUsage']
        self.upTime = values['UpTime']
        self.cpuTemperature = values['CPUtemp']        

    def run(self):
        self.setupNTTopics()
        while(True):
            self.getSystemValues()
            self.publishValues()
            sleep(5)


if __name__ == "__main__":
    SysInfoPublisher().run()

