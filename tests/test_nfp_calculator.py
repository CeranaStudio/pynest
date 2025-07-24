import unittest
from nester.nfp_calculator import NFPCalculator
from nester.geometry_utils import GeometryUtils


class TestNFPCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Simple rectangles
        self.rect_a = [
            {'x': 0, 'y': 0},
            {'x': 10, 'y': 0},
            {'x': 10, 'y': 6},
            {'x': 0, 'y': 6}
        ]
        
        self.rect_b = [
            {'x': 0, 'y': 0},
            {'x': 4, 'y': 0},
            {'x': 4, 'y': 3},
            {'x': 0, 'y': 3}
        ]
        
        # Triangle
        self.triangle = [
            {'x': 0, 'y': 0},
            {'x': 6, 'y': 0},
            {'x': 3, 'y': 4}
        ]
    
    def test_cache_key_generation(self):
        """Test NFP cache key generation"""
        key1 = NFPCalculator.cache_key('A', 'B', True, 0, 90)
        key2 = NFPCalculator.cache_key('A', 'B', True, 0, 90)
        key3 = NFPCalculator.cache_key('A', 'B', False, 0, 90)
        
        # Same parameters should generate same key
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different keys
        self.assertNotEqual(key1, key3)
    
    def test_nfp_rectangle_container(self):
        """Test NFP calculation for rectangle container"""
        # Test inner NFP with rectangle container
        nfp = NFPCalculator._nfp_rectangle(self.rect_a, self.rect_b)
        
        self.assertIsInstance(nfp, list)
        self.assertGreater(len(nfp), 0)
        
        if nfp:
            # NFP should be a valid polygon
            nfp_polygon = nfp[0]
            self.assertGreaterEqual(len(nfp_polygon), 3)
            
            # NFP bounds should be smaller than container bounds
            nfp_bounds = GeometryUtils.get_polygon_bounds(nfp_polygon)
            container_bounds = GeometryUtils.get_polygon_bounds(self.rect_a)
            part_bounds = GeometryUtils.get_polygon_bounds(self.rect_b)
            
            expected_width = container_bounds['width'] - part_bounds['width']
            expected_height = container_bounds['height'] - part_bounds['height']
            
            self.assertAlmostEqual(nfp_bounds['width'], expected_width, places=3)
            self.assertAlmostEqual(nfp_bounds['height'], expected_height, places=3)
    
    def test_minkowski_difference(self):
        """Test Minkowski difference calculation"""
        nfp = NFPCalculator._minkowski_difference(self.rect_a, self.rect_b)
        
        self.assertIsInstance(nfp, list)
        # Minkowski difference should produce at least one polygon
        if nfp:
            self.assertGreaterEqual(len(nfp[0]), 3)
    
    def test_calculate_nfp_inner(self):
        """Test inner NFP calculation"""
        # Test with rectangle (should use rectangle method)
        nfp_rect = NFPCalculator.calculate_nfp(self.rect_a, self.rect_b, inside=True)
        self.assertIsInstance(nfp_rect, list)
        
        # Test with triangle (should use polygon method)
        nfp_tri = NFPCalculator.calculate_nfp(self.triangle, self.rect_b, inside=True)
        self.assertIsInstance(nfp_tri, list)
    
    def test_calculate_nfp_outer(self):
        """Test outer NFP calculation"""
        nfp = NFPCalculator.calculate_nfp(self.rect_a, self.rect_b, inside=False)
        self.assertIsInstance(nfp, list)
    
    def test_clipper_coordinate_conversion(self):
        """Test coordinate conversion for clipper"""
        # Test conversion to clipper coordinates
        clipper_coords = NFPCalculator._to_clipper_coords(self.rect_a)
        self.assertEqual(len(clipper_coords), len(self.rect_a))
        
        # Each coordinate should be scaled
        for i, coord in enumerate(clipper_coords):
            self.assertEqual(coord[0], int(self.rect_a[i]['x'] * 1000000))
            self.assertEqual(coord[1], int(self.rect_a[i]['y'] * 1000000))
        
        # Test conversion back from clipper coordinates
        converted_back = NFPCalculator._from_clipper_coords(clipper_coords)
        self.assertEqual(len(converted_back), len(self.rect_a))
        
        # Coordinates should be approximately equal after round trip
        for i, point in enumerate(converted_back):
            self.assertAlmostEqual(point['x'], self.rect_a[i]['x'], places=5)
            self.assertAlmostEqual(point['y'], self.rect_a[i]['y'], places=5)
    
    def test_empty_polygon_handling(self):
        """Test handling of empty or invalid polygons"""
        empty_polygon = []
        
        # Should handle empty polygons gracefully
        nfp = NFPCalculator.calculate_nfp(empty_polygon, self.rect_b, inside=True)
        self.assertIsInstance(nfp, list)
        
        nfp = NFPCalculator.calculate_nfp(self.rect_a, empty_polygon, inside=False)
        self.assertIsInstance(nfp, list)
    
    def test_nfp_polygon_inside(self):
        """Test polygon inside NFP calculation"""
        nfp = NFPCalculator._nfp_polygon_inside(self.triangle, self.rect_b)
        self.assertIsInstance(nfp, list)
        
        # If NFP is calculated, it should be valid polygons
        for polygon in nfp:
            self.assertGreaterEqual(len(polygon), 3)
            for point in polygon:
                self.assertIn('x', point)
                self.assertIn('y', point)
                self.assertIsInstance(point['x'], (int, float))
                self.assertIsInstance(point['y'], (int, float))


if __name__ == '__main__':
    unittest.main()