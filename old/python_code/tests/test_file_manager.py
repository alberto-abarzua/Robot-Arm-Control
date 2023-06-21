import os.path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arm_utils.filemanager as filem
import unittest
import arm_control.controller as ctrl
from arm_utils.armTransforms import Angle
from arm_utils.armTransforms import Config
from arm_utils.armTransforms import generate_curve_ptp
import numpy as np
from pathlib import Path
__author__ = "Alberto Abarzua"


class file_manager_test(unittest.TestCase):

    def angleAllClose(self, L1, L2):
        """Helper method used to check if two Angle list have almost the same values.

        Args:
            L1 (list[Angle]): first list
            L2 (list[Angle]): second list
        Returns:
            bool: if all the angles are close.
        """
        L1 = [angle.rad for angle in L1]
        L2 = [angle.rad for angle in L2]
        return np.allclose(L1, L2, atol=1 / 1000)

    def test_instructions(self):
        p1 = Config([300, 0, 300], [Angle(0, "rad"), Angle(0, "rad"), Angle(0, "rad")])
        p2 = Config([320, 0, 320], [Angle(0, "rad"), Angle(90, "deg"), Angle(0, "rad")])

        p1_instruction = filem.CordAngleInstruction(p1)
        p2_instruction = filem.CordAngleInstruction(p2)

        self.assertEqual("c 300 0 300 0 0 0\n", p1_instruction.line)
        self.assertEqual("c 320 0 320 0 1.57079633 0\n", p2_instruction.line)
        p2_fromstring = filem.CordAngleInstruction(
            "c 320 0 320 0 1.57079633 0\n")
        self.assertEqual("c 320 0 320 0 1.57079633 0\n", p2_fromstring.line)
        self.assertEqual(p2.cords, p2_fromstring.as_config().cords)
        self.assertTrue(self.angleAllClose(p2.euler_angles, p2_fromstring.as_config().euler_angles))

        sleep_instruct = filem.SleepInstruction(0.5)
        self.assertEqual(sleep_instruct.line, "s 0.500\n")
        sleep_from_string = filem.SleepInstruction("s 0.500\n")
        self.assertEqual(sleep_from_string.value, 0.5)

    def test_run(self):
        self.controller.monitor.arduino.set_log_file("test1_arduino.txt")
        p1 = Config([359, 0, 345], [Angle(0, "deg"),
                                    Angle(0, "deg"), Angle(0, "deg")])
        p2 = Config([357, -2.67, 300.49], [Angle(0, "deg"), Angle(-20.73, "deg"), Angle(-39.58, "deg")])
        curve = generate_curve_ptp(p1=p1, p2=p2, n=100)

        f = filem.FileManager()
        instructions = f.from_curve_to_instruct(curve)
        f.write_file(instructions, "test1.txt")
        run_f= Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"arm_control","data","test1.txt"))
        self.controller.run_file(run_f)
        while (self.controller.step()):
            continue
        self.controller.monitor.arduino.log.close()
        f1 = open(self.path.joinpath("expected_test1_arduino.txt"), "r")
        f2 = open(self.path.joinpath("test1_arduino.txt"), "r")
        self.assertEqual(f1.readlines(), f2.readlines())
        f1.close()
        f2.close()

    def setUp(self) -> None:
        self.controller = ctrl.Controller()
        self.controller.robot.a2x = 0
        self.controller.robot.a2z = 172.48
        self.controller.robot.a3z = 173.5
        self.controller.robot.a4z = 0

        self.controller.robot.a4x = 126.2
        self.controller.robot.a5x = 64.1
        self.controller.robot.a6x = 169
        self.controller.acc = 10000
        # physical constraints
        p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = Path(os.path.join(p,"tests","test_data"))
        self.controller.robot.j1_range = lambda x: x > -np.pi / 2 and x < np.pi / 2
        self.controller.robot.j2_range = lambda x: x > -1.39626 and x < 1.57
        self.controller.robot.j3_range = lambda x: x > -np.pi / 2 and x < np.pi / 2
        self.controller.robot.j5_range = lambda x: x > -np.pi / 2 and x < np.pi / 2


if __name__ == '__main__':
    unittest.main()
