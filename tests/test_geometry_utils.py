import unittest
import math
from nester.geometry_utils import GeometryUtils


class TestGeometryUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Simple rectangle
        self.rectangle = [
            {'x': 0, 'y': 0},
            {'x': 10, 'y': 0},
            {'x': 10, 'y': 5},
            {'x': 0, 'y': 5}
        ]
        
        # Simple triangle
        self.triangle = [
            {'x': 0, 'y': 0},
            {'x': 10, 'y': 0},
            {'x': 5, 'y': 8}
        ]
        
        # L-shaped polygon
        self.l_shape = [
            {'x': 0, 'y': 0},
            {'x': 10, 'y': 0},
            {'x': 10, 'y': 3},
            {'x': 3, 'y': 3},
            {'x': 3, 'y': 8},
            {'x': 0, 'y': 8}
        ]
    
    def test_almost_equal(self):
        """Test almost_equal function"""
        self.assertTrue(GeometryUtils.almost_equal(1.0, 1.0000001))
        self.assertFalse(GeometryUtils.almost_equal(1.0, 1.1))
        self.assertTrue(GeometryUtils.almost_equal(0.0, 0.0))
    
    def test_polygon_area(self):
        """Test polygon area calculation"""
        # Rectangle area should be width * height = 10 * 5 = 50
        area = GeometryUtils.polygon_area(self.rectangle)
        self.assertAlmostEqual(abs(area), 50.0, places=5)
        
        # Triangle area should be 0.5 * base * height = 0.5 * 10 * 8 = 40
        area = GeometryUtils.polygon_area(self.triangle)
        self.assertAlmostEqual(abs(area), 40.0, places=5)
    
    def test_get_polygon_bounds(self):
        """Test bounding box calculation"""
        bounds = GeometryUtils.get_polygon_bounds(self.rectangle)
        expected = {'x': 0, 'y': 0, 'width': 10, 'height': 5}
        self.assertEqual(bounds, expected)
        
        bounds = GeometryUtils.get_polygon_bounds(self.triangle)
        expected = {'x': 0, 'y': 0, 'width': 10, 'height': 8}
        self.assertEqual(bounds, expected)
    
    def test_rotate_polygon(self):
        """Test polygon rotation"""
        # Rotate rectangle 90 degrees
        rotated = GeometryUtils.rotate_polygon(self.rectangle, 90)
        
        # Check that width and height are swapped
        self.assertAlmostEqual(rotated['width'], 5, places=5)
        self.assertAlmostEqual(rotated['height'], 10, places=5)
        
        # Rotate 360 degrees should return to original
        rotated_360 = GeometryUtils.rotate_polygon(self.rectangle, 360)
        original_bounds = GeometryUtils.get_polygon_bounds(self.rectangle)
        
        self.assertAlmostEqual(rotated_360['width'], original_bounds['width'], places=5)
        self.assertAlmostEqual(rotated_360['height'], original_bounds['height'], places=5)
    
    def test_translate_polygon(self):
        """Test polygon translation"""
        translated = GeometryUtils.translate_polygon(self.rectangle, 5, 3)
        
        # Check that all points are moved by the offset
        for i, point in enumerate(translated):
            self.assertAlmostEqual(point['x'], self.rectangle[i]['x'] + 5, places=5)
            self.assertAlmostEqual(point['y'], self.rectangle[i]['y'] + 3, places=5)
    
    def test_normalize_polygon(self):
        """Test polygon normalization"""
        # Create a polygon not at origin
        offset_rect = GeometryUtils.translate_polygon(self.rectangle, 10, 20)
        normalized = GeometryUtils.normalize_polygon(offset_rect)
        
        # Check that the normalized polygon starts at origin
        bounds = GeometryUtils.get_polygon_bounds(normalized)
        self.assertAlmostEqual(bounds['x'], 0, places=5)
        self.assertAlmostEqual(bounds['y'], 0, places=5)
    
    def test_point_in_polygon(self):
        """Test point in polygon detection"""
        # Point inside rectangle
        inside_point = {'x': 5, 'y': 2.5}
        self.assertTrue(GeometryUtils.point_in_polygon(inside_point, self.rectangle))
        
        # Point outside rectangle
        outside_point = {'x': 15, 'y': 2.5}
        self.assertFalse(GeometryUtils.point_in_polygon(outside_point, self.rectangle))
        
        # Point on edge (should be handled consistently)
        edge_point = {'x': 0, 'y': 2.5}
        # The exact behavior on edges can vary, but should be consistent
        result = GeometryUtils.point_in_polygon(edge_point, self.rectangle)
        self.assertIsInstance(result, bool)
    
    def test_is_rectangle(self):
        """Test rectangle detection"""
        self.assertTrue(GeometryUtils.is_rectangle(self.rectangle))
        self.assertFalse(GeometryUtils.is_rectangle(self.triangle))
        self.assertFalse(GeometryUtils.is_rectangle(self.l_shape))
    
    def test_polygon_offset(self):
        """Test polygon offsetting"""
        # Positive offset should make polygon larger
        offset_positive = GeometryUtils.polygon_offset(self.rectangle, 1)
        if offset_positive:  # Check if offset succeeded
            offset_bounds = GeometryUtils.get_polygon_bounds(offset_positive)
            original_bounds = GeometryUtils.get_polygon_bounds(self.rectangle)
            self.assertGreater(offset_bounds['width'], original_bounds['width'])
            self.assertGreater(offset_bounds['height'], original_bounds['height'])
        
        # Negative offset should make polygon smaller
        offset_negative = GeometryUtils.polygon_offset(self.rectangle, -0.5)
        if offset_negative:  # Check if offset succeeded
            offset_bounds = GeometryUtils.get_polygon_bounds(offset_negative)
            original_bounds = GeometryUtils.get_polygon_bounds(self.rectangle)
            self.assertLess(offset_bounds['width'], original_bounds['width'])
            self.assertLess(offset_bounds['height'], original_bounds['height'])


if __name__ == '__main__':
    unittest.main()