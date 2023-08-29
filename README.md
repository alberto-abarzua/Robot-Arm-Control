# 6DOF Robotic Arm Control System

## Description

The project comprises a control system for a 6DOF robotic arm.
 The system is split into two key parts: a controller and a firmware.

## Controller

The controller forms the core of our system, housed within a Python 
script that is executed on a computer. The role of the controller is two-fold. 
It sends commands to the firmware, while simultaneously receiving data from it. 
As the primary interface for the user, it provides a programmable interface for the 
manipulation and operation of the robotic arm.

## Firmware

In contrast to the controller, the firmware is designed to run on an 
ESP32 microcontroller or on a computer for testing purposes. It is coded in C++ and 
designed to be as platform-independent as possible, making future porting to other 
microcontrollers feasible. The firmware takes commands from the controller, 
executing them accordingly. Additionally, it undertakes the responsibility of forwarding data 
to the controller.

![System diagram](docs/imgs/controller-firmware.png)

## Features

-   [x] Basic control of the robotic arm using a Python script
-   [x] CI/CD pipeline for the controller and the firmware (lint, format, test, build)
-   [x] Firmware compatibility with an ESP32 microcontroller
-   [x] Firmware compatibility with a computer
-   [x] Firmware can be tested on a computer
-   [x] Firmware can be tested on an ESP32 microcontroller
-   [x] Communication between controller and firmware via WiFi TCP socket
-   [x] Implementing Inverse Kinematics for the robotic arm
-   [x] Implementing Forward Kinematics for the robotic arm
-   [x] Implementing a basic controller for the robotic arm
-   [x] Implementing a basic firmware for the robotic arm
-   [x] Support for 6DOF robotic arm
-   [x] Python controller is a python package on [PyPI](https://pypi.org/project/robot-arm-controller/) 


## How to run

### Requirements

-   Docker and Docker compose
    -   [Get Docker](https://docs.docker.com/get-docker/)

### Run

Firstly, clone this repository. After that, execute the command `./run.sh` in the root
 directory of the project. This will execute the `controller/src/main.py` script along with the 
 `firmware` service.

#### Useful commands

```bash
# Run the controller main.py and the firmware (default)
./manage.py runserver

# Lint the controller code
./manage.py lint

# Format firmware and controller code
./manage.py format

# Run the tests
./manage.py test

# Check build for esp-idf (no dependencies needed)
./manage.py build-esp

# Run tests for the esp (esp-idf needed)
./manage.py test-esp
```
