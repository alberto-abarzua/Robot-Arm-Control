import sys
import os.path


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inputs import get_gamepad
import math
import threading
import time
from arm_utils import filemanager
from arm_utils.armTransforms import Angle
class XboxController(object):
    """XboxController class, used to get inputs from an xbox controller.

    """
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        """XboxController, creates buttons dictionary and starts the monitor thread.
        """
        self.buttons = {
            "buttons" : 0,
            "LeftJoystickY" : 0,
            "LeftJoystickX" : 0,
            "RightJoystickY" : 0,
            "RightJoystickX" : 0,
            "LeftTrigger" : 0,
            "RightTrigger" : 0,
            "LeftBumper" : 0,
            "RightBumper" : 0,
            "A" : 0,
            "X" : 0,
            "Y" : 0,
            "B" : 0,
            "LeftThumb" : 0,
            "RightThumb" : 0,
            "Back" : 0,
            "Start" : 0,
            "LeftDPad" : 0,
            "RightDPad" : 0,
            "UpDPad" : 0,
            "DownDPad" : 0
            }

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()


    def clean_trigger(self,val):
        """Used to get a clean value from a trigger event

        Args:
            val (float): input form trigger event

        Returns:
            int: cleaned value
        """
        tolerance = 0.1
        pre = val/XboxController.MAX_TRIG_VAL
        if (abs(pre)<tolerance):
            return 0
        return pre
    def clean_joy(self,val):
        """Used to get a clean value from a joystick event

        Args:
            val (float): input form trigger event

        Returns:
            int: cleaned value
        """
        tolerance = 0.3
        pre = val/XboxController.MAX_JOY_VAL
        if (abs(pre)<tolerance):
            return 0
        return pre

    def _monitor_controller(self):
        """Gets the events from the gamepad and modifies the buttons dictionary accordingly
        """
        while True:
            try:
                events = get_gamepad()

            except Exception as e:
                print(e)
                return
                
            for event in events:
                if event.code == 'ABS_Y':
                    self.buttons["LeftJoystickY"] = self.clean_joy(event.state)
                elif event.code == 'ABS_X':
                    self.buttons["LeftJoystickX"] = self.clean_joy(event.state) # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.buttons["RightJoystickY"] = self.clean_joy(event.state) # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.buttons["RightJoystickX"] = self.clean_joy(event.state) # normalize between -1 and 1

                elif event.code == 'ABS_Z':
                    self.buttons["LeftTrigger"] = self.clean_trigger(event.state)# normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.buttons["RightTrigger"] = self.clean_trigger(event.state)# normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.buttons["LeftBumper"] = event.state
                elif event.code == 'BTN_TR':
                    self.buttons["RightBumper"] = event.state
                elif event.code == 'BTN_SOUTH':
                    self.buttons["A"] = event.state
                elif event.code == 'BTN_NORTH':
                    self.buttons["X"] = event.state
                elif event.code == 'BTN_WEST':
                    self.buttons["Y"] = event.state
                elif event.code == 'BTN_EAST':
                    self.buttons["B"] = event.state
                elif event.code == 'BTN_THUMBL':
                    self.buttons["LeftThumb"] = event.state
                elif event.code == 'BTN_THUMBR':
                    self.buttons["RightThumb"] = event.state
                elif event.code == 'BTN_SELECT':
                    self.buttons["Start"] = event.state
                elif event.code == 'BTN_START':
                    self.buttons["Back"] = event.state
                elif event.code == 'ABS_HAT0X' :
                    if(event.state==-1):
                        self.buttons["LeftDPad"] = abs(event.state)
                    elif(event.state ==1):
                        self.buttons["RightDPad"] = abs(event.state)
                    else:
                        self.buttons["LeftDPad"] = abs(event.state)
                        self.buttons["RightDPad"] = abs(event.state)

                elif event.code == 'ABS_HAT0Y' :
                    if(event.state==-1):
                        self.buttons["UpDPad"] = abs(event.state)
                    elif(event.state ==1):
                        self.buttons["DownDPad"] = abs(event.state)
                    else:
                        self.buttons["UpDPad"] = abs(event.state)
                        self.buttons["DownDPad"] = abs(event.state)



class ArmGamePad:
    """ArmGamePad, uses an XboxController to control the postion and euler angles of the arm. Moves the arm joints to their positions.
    """

    def __init__(self,controller) -> None:
        """Starts the gamepad xbox controller.

        Args:
            controller (Controller): arm controller wich will receive the positional information from the GamePad.
        """

        self.joy = XboxController()
        self.buttons =self.joy.buttons 
        self.controller = controller
        self.robot = self.controller.robot
        #steps
        self.dir_step = 70
        self.angle_step = 0.3
        self.tool_step =80
        self.fps = 60
        

    def run(self):
        """Starts the main loop of the controlls.
        """
        t0 = time.perf_counter()
        sign = lambda x :math.copysign(1,x)
        while(True):
            t1 = time.perf_counter()
            dt = t1 - t0
            t0 = t1
            self.robot.direct_kinematics()  # We update the euler angles and xyz
            xyz,euler_angles,tool = self.robot.config.cords,self.robot.config.euler_angles,self.robot.config.tool
            #Previous state:
            x, y,z = xyz
            A, B,C = euler_angles
            tang = tool
            #CONTROLS FOR POSITIONS

            b = self.buttons
            #---y---
            if(b["LeftJoystickX"] !=0):
                y+= sign(b["LeftJoystickX"] )*self.dir_step*dt
            #---x---
            if(b["LeftJoystickY"] !=0):
                x+= sign(b["LeftJoystickY"] )*self.dir_step*dt

            #---Z Down
            if(b["LeftTrigger"] !=0):
                z-= self.dir_step*dt
            
            #---Z up
            if(b["RightTrigger"] !=0):
                z+= self.dir_step*dt
            
            angle_step_positive = Angle(self.angle_step*dt, "rad")
            angle_step_negative = Angle(-self.angle_step*dt, "rad")


            #-- A --

            if(b["LeftBumper"] !=0):
                A.add(angle_step_negative)
                A.add(angle_step_negative)
                A.add(angle_step_negative)


            if(b["RightBumper"] !=0):
                A.add(angle_step_positive)
                A.add(angle_step_positive)
                A.add(angle_step_positive)

                   
            # -- B --

            if(b["RightJoystickY"] !=0):
                if(sign(b["RightJoystickY"] )>=0):
                    B.add(angle_step_positive)
                else:
                    B.add(angle_step_negative)

             #-- C --

            if(b["RightJoystickX"] !=0):
                if(sign(b["RightJoystickX"] )>=0):
                    C.add(angle_step_positive)
                else:
                    C.add(angle_step_negative)
            if(b["Back"]!=0): #Try and home the arm
                self.controller.home_arm()
                continue
            

            #tools controls:

            if(b["LeftDPad"] != 0):
                tang+=dt*self.tool_step

            if(b["RightDPad"] != 0):
                tang-=dt*self.tool_step


            try:
                self.controller.move_to_point(filemanager.Config([x, y, z], [A, B,C],round(tang)))
                assert  self.controller.coms_lock.locked() == False #Check that the controller arduino is not BUSY
            except Exception as e:
                print(e)
                x, y,z = xyz
                A, B,C = euler_angles
                tang = tool


            time.sleep(max(0,(1/self.fps)-dt)) #adjust for the required fps

if __name__ == '__main__':
    """ Used to test the inputs of the xbox controller."""
    joy = XboxController()
    while True:
        print(joy.buttons) #Print the inputs.