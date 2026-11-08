"""Run: python -m unittest discover -s code -p 'test_*.py' -v"""
import csv
import unittest
from pathlib import Path
import cv2
import numpy as np
from detect_corners import object_grid, detect, refine, displacement

class CornerValidation(unittest.TestCase):
    def test_grid_units_and_order(self):
        grid=object_grid().reshape(7,11,3)
        np.testing.assert_allclose(np.diff(grid,axis=1),np.broadcast_to([30,0,0],(7,10,3)))
        np.testing.assert_allclose(np.diff(grid,axis=0),np.broadcast_to([0,30,0],(6,11,3)))
        np.testing.assert_array_equal(grid[0,0],[0,0,0])
        np.testing.assert_array_equal(grid[-1,-1],[300,180,0])
        for square in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):object_grid(square_mm=square)

    def test_synthetic_board_and_copy_isolation(self):
        gray=np.full((520,720),255,np.uint8)
        for y in range(8):
            for x in range(12):
                gray[60+y*40:60+(y+1)*40,100+x*40:100+(x+1)*40]=(x+y)%2*255
        a=detect(gray);saved=a.copy();b=refine(gray,a)
        np.testing.assert_array_equal(a,saved)
        self.assertEqual(b.shape,(77,1,2))
        # Analytic intersections are at pixel boundary half positions.
        expected=np.array([(139.5+x*40,99.5+y*40) for y in range(7) for x in range(11)])
        np.testing.assert_allclose(b[:,0],expected,atol=.02)
        with self.assertRaises(ValueError):detect(np.full((576,1024),127,np.uint8))

    def test_export_matches_independent_csv(self):
        root=Path(__file__).resolve().parent/'results/corners'
        with np.load(root/'corners.npz',allow_pickle=False) as z:
            self.assertEqual(z['image_points_refined'].shape,(4,77,1,2))
            self.assertEqual(z['object_points'].dtype,np.float32)
            self.assertEqual(z['image_points_refined'].dtype,np.float32)
            with (root/'points.csv').open(encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),308)
            expected=np.array([[float(r['refined_u']),float(r['refined_v'])] for r in rows])
            np.testing.assert_allclose(expected,z['image_points_refined'].reshape(-1,2),atol=1e-7)
            shifts=displacement(z['image_points_initial'],z['image_points_refined'])
            np.testing.assert_allclose(shifts,[float(r['shift_px']) for r in rows],atol=1e-10)
            self.assertTrue(np.isfinite(expected).all())
            self.assertTrue(((expected[:,0]>=0)&(expected[:,0]<1024)&(expected[:,1]>=0)&(expected[:,1]<576)).all())

if __name__=='__main__':unittest.main()
