#!/usr/bin/env python3
from __future__ import annotations

import signal
import socket
import time
from sys import exit
from typing import TYPE_CHECKING

import ntcore
import psutil

import config

if TYPE_CHECKING:
    from ntcore import (
        DoublePublisher,
        NetworkTable,
        NetworkTableInstance,
        StringPublisher,
    )


class Publisher:
    LOGGING_MAP = (("_system_load", "getDoubleTopic"), ("_ip_address", "getStringTopic"), 
                   ("_memory_usage", "getDoubleTopic"), ("_up_time", "getStringTopic"), 
                   ("_cpu_temperature", "getDoubleTopic"))

    _system_load: DoublePublisher
    _ip_address: StringPublisher
    _memory_usage: DoublePublisher
    _up_time: StringPublisher
    _cpu_temperature: DoublePublisher

    def __init__(self, nt: NetworkTableInstance = ntcore.NetworkTableInstance.getDefault()) -> None:
        nt.startClient4(config.NT_IDENTITY)
        nt.setServerTeam(config.TEAM_NUMBER)
        # nt.setServer(config.SERVER_NAME, ntcore.NetworkTableInstance.kDefaultPort4)
        table: NetworkTable = nt.getTable(config.NT_TABLE)
    
        for name, getter in self.LOGGING_MAP:
            publisher: DoublePublisher | StringPublisher = getattr(table, getter)(name[1:]).publish()

            if isinstance(publisher, ntcore.DoublePublisher):
                value = 0
            else:
                value = "0"
            
            publisher.setDefault(value)

            setattr(self, name, publisher)

        psutil.getloadavg() # see https://psutil.readthedocs.io/en/latest/index.html#psutil.getloadavg

    def publish(self) -> None:
        for name, _ in self.LOGGING_MAP:
            getter = getattr(self, name[1:])
            getter = getter
        
    @property
    def system_load(self) -> float:
        return psutil.getloadavg()[0] / psutil.cpu_count() * 100
    
    @system_load.setter
    def system_load(self, value: float) -> None:
        self._system_load.set(value)
    
    @property
    def ip_address(self) -> StringPublisher:
        return socket.gethostbyname(socket.gethostname())
    
    @ip_address.setter
    def ip_address(self, value: str) -> None:
        self._ip_address.set(value)

    @property
    def memory_usage(self) -> DoublePublisher:
        return psutil.virtual_memory().percent
    
    @memory_usage.setter
    def memory_usage(self, value: float) -> None:
        self._memory_usage.set(value)

    @property
    def up_time(self) -> StringPublisher:
        return time.monotonic() / 60
    
    @up_time.setter
    def up_time(self, value: str) -> None:
        self._up_time.set(value)

    @property
    def cpu_temperature(self) -> DoublePublisher:
        return 0
        return psutil.sensors_temperatures()["cpu-thermal"].current # might be broken
    
    @cpu_temperature.setter
    def cpu_temperature(self, value: float) -> None:
        self._cpu_temperature.set(value)


def main():
    signal.signal(signal.SIGINT, lambda *_: exit(0))
    signal.signal(signal.SIGTERM, lambda *_: exit(0))

    publisher = Publisher()

    while True:
        publisher.publish()
        time.sleep(5)

if __name__ == "__main__":
    main()

