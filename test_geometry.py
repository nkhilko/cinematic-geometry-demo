import math
import unittest
from xml.etree import ElementTree

from geometry import camera, contact_sheet, CORNERS, inspect, project


class GeometryTest(unittest.TestCase):
    def test_two_phase_target_lock_and_final_framing(self):
        poses = [camera(frame / 50) for frame in range(51)]
        result = inspect(poses)
        self.assertAlmostEqual(result["final_width_fraction"], 0.84)
        self.assertAlmostEqual(result["final_artwork_aspect"], 0.75)
        self.assertLess(result["max_target_error_px"], 1e-9)
        opening = [project(corner, poses[0]) for corner in CORNERS]
        self.assertNotAlmostEqual(opening[3][1] - opening[0][1], opening[2][1] - opening[1][1])
        self.assertAlmostEqual(math.hypot(*[poses[0][i] for i in (0, 2)]), 4.6)

    def test_phase_boundary_and_svg(self):
        self.assertLess(math.dist(camera(0.6 - 1e-6), camera(0.6 + 1e-6)), 1e-8)
        self.assertGreater(camera(0.61)[2], camera(1)[2])
        sheet = ElementTree.fromstring(contact_sheet([camera(n / 50) for n in range(51)]))
        self.assertEqual(sum(node.tag.endswith("polygon") for node in sheet.iter()), 9)

    def test_rejects_invalid_time_and_points_behind_camera(self):
        with self.assertRaises(ValueError):
            camera(1.1)
        with self.assertRaises(ValueError):
            project((0, 0, 90), camera(1))
