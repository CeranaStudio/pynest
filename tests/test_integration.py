import unittest
import tempfile
import os
from nester import Nester
from nester.dxf_handler import DXFHandler


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete nesting workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test polygons
        self.container_points = [
            {'x': 0, 'y': 0},
            {'x': 50, 'y': 0},
            {'x': 50, 'y': 30},
            {'x': 0, 'y': 30}
        ]
        
        self.parts_data = [
            # Rectangle 1
            [
                {'x': 0, 'y': 0},
                {'x': 8, 'y': 0},
                {'x': 8, 'y': 5},
                {'x': 0, 'y': 5}
            ],
            # Rectangle 2
            [
                {'x': 0, 'y': 0},
                {'x': 6, 'y': 0},
                {'x': 6, 'y': 4},
                {'x': 0, 'y': 4}
            ],
            # Triangle
            [
                {'x': 0, 'y': 0},
                {'x': 7, 'y': 0},
                {'x': 3.5, 'y': 6}
            ],
            # Small rectangle
            [
                {'x': 0, 'y': 0},
                {'x': 4, 'y': 0},
                {'x': 4, 'y': 3},
                {'x': 0, 'y': 3}
            ]
        ]
    
    def test_complete_nesting_workflow(self):
        """Test complete nesting workflow from start to finish"""
        # Configuration for quick test
        config = {
            'spacing': 1,
            'rotations': 4,
            'population_size': 8,
            'mutation_rate': 15,
            'max_generations': 20,
            'curve_tolerance': 0.3
        }
        
        # Initialize nester
        nester = Nester(config)
        
        # Add container and parts
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        # Track progress
        progress_history = []
        def progress_callback(stats):
            progress_history.append(stats)
        
        # Run nesting
        result = nester.run(progress_callback=progress_callback)
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIn('fitness', result)
        self.assertIn('placed_count', result)
        self.assertIn('total_parts', result)
        self.assertIn('utilization', result)
        self.assertIn('placements', result)
        
        # Check that algorithm made progress
        self.assertGreater(len(progress_history), 0)
        self.assertEqual(result['total_parts'], len(self.parts_data))
        self.assertGreaterEqual(result['placed_count'], 0)
        self.assertLessEqual(result['placed_count'], result['total_parts'])
        
        # Check utilization is reasonable
        self.assertGreaterEqual(result['utilization'], 0)
        self.assertLessEqual(result['utilization'], 1)
        
        # Get placement data
        placement_data = nester.get_placement_data()
        
        if result['placed_count'] > 0:
            self.assertIsNotNone(placement_data)
            self.assertGreater(len(placement_data), 0)
            
            # Verify placement data structure
            for bin_data in placement_data:
                self.assertIn('container', bin_data)
                self.assertIn('parts', bin_data)
                
                # Check that placed parts have valid coordinates
                for part in bin_data['parts']:
                    self.assertIsInstance(part['x'], (int, float))
                    self.assertIsInstance(part['y'], (int, float))
                    self.assertIn(part['rotation'], [0, 90, 180, 270])  # 4 rotations
    
    def test_nesting_with_different_configurations(self):
        """Test nesting with various configuration parameters"""
        base_config = {
            'population_size': 5,
            'max_generations': 10
        }
        
        test_configs = [
            # Test different spacing
            {**base_config, 'spacing': 0, 'rotations': 2},
            {**base_config, 'spacing': 2, 'rotations': 2},
            
            # Test different rotations
            {**base_config, 'spacing': 0, 'rotations': 1},  # No rotation
            {**base_config, 'spacing': 0, 'rotations': 8},  # Many rotations
            
            # Test different mutation rates
            {**base_config, 'spacing': 0, 'rotations': 4, 'mutation_rate': 5},
            {**base_config, 'spacing': 0, 'rotations': 4, 'mutation_rate': 30},
        ]
        
        for i, config in enumerate(test_configs):
            with self.subTest(config_index=i):
                nester = Nester(config)
                nester.add_container(self.container_points)
                nester.add_parts(self.parts_data[:2])  # Use fewer parts for speed
                
                result = nester.run()
                
                # Should always return a valid result
                self.assertIsNotNone(result)
                self.assertIn('fitness', result)
                self.assertIn('placed_count', result)
    
    def test_challenging_nesting_scenario(self):
        """Test with a challenging nesting scenario"""
        # Small container
        small_container = [
            {'x': 0, 'y': 0},
            {'x': 15, 'y': 0},
            {'x': 15, 'y': 10},
            {'x': 0, 'y': 10}
        ]
        
        # Parts that are difficult to fit
        challenging_parts = [
            # Large rectangle (might not fit)
            [
                {'x': 0, 'y': 0},
                {'x': 12, 'y': 0},
                {'x': 12, 'y': 8},
                {'x': 0, 'y': 8}
            ],
            # Medium rectangle
            [
                {'x': 0, 'y': 0},
                {'x': 6, 'y': 0},
                {'x': 6, 'y': 4},
                {'x': 0, 'y': 4}
            ],
            # Small square
            [
                {'x': 0, 'y': 0},
                {'x': 3, 'y': 0},
                {'x': 3, 'y': 3},
                {'x': 0, 'y': 3}
            ]
        ]
        
        config = {
            'spacing': 0.5,
            'rotations': 4,
            'population_size': 10,
            'max_generations': 30
        }
        
        nester = Nester(config)
        nester.add_container(small_container)
        nester.add_parts(challenging_parts)
        
        result = nester.run()
        
        # Should handle the challenging scenario gracefully
        self.assertIsNotNone(result)
        
        # Might not place all parts due to space constraints
        self.assertLessEqual(result['placed_count'], len(challenging_parts))
        
        # But should place at least some parts if possible
        # (This might fail if the algorithm can't place anything, which is acceptable)
        if result['placed_count'] > 0:
            placement_data = nester.get_placement_data()
            self.assertIsNotNone(placement_data)
    
    def test_nesting_with_irregular_shapes(self):
        """Test nesting with irregular (non-rectangular) shapes"""
        # L-shaped container
        l_container = [
            {'x': 0, 'y': 0},
            {'x': 20, 'y': 0},
            {'x': 20, 'y': 8},
            {'x': 8, 'y': 8},
            {'x': 8, 'y': 20},
            {'x': 0, 'y': 20}
        ]
        
        # Various irregular parts
        irregular_parts = [
            # L-shaped part
            [
                {'x': 0, 'y': 0},
                {'x': 6, 'y': 0},
                {'x': 6, 'y': 3},
                {'x': 3, 'y': 3},
                {'x': 3, 'y': 6},
                {'x': 0, 'y': 6}
            ],
            # Triangle
            [
                {'x': 0, 'y': 0},
                {'x': 5, 'y': 0},
                {'x': 2.5, 'y': 4}
            ],
            # Pentagon
            [
                {'x': 2, 'y': 0},
                {'x': 4, 'y': 0},
                {'x': 5, 'y': 2},
                {'x': 3, 'y': 4},
                {'x': 1, 'y': 2}
            ]
        ]
        
        config = {
            'spacing': 0.5,
            'rotations': 8,  # More rotations for irregular shapes
            'population_size': 12,
            'max_generations': 25,
            'explore_concave': True  # Enable for better irregular shape handling
        }
        
        nester = Nester(config)
        nester.add_container(l_container)
        nester.add_parts(irregular_parts)
        
        result = nester.run()
        
        # Should handle irregular shapes
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result['placed_count'], 0)
    
    def test_large_number_of_parts(self):
        """Test with a larger number of parts"""
        # Create many small parts
        many_parts = []
        for i in range(15):
            # Create small squares with slight size variations
            size = 3 + (i % 3)  # Sizes 3, 4, 5
            part = [
                {'x': 0, 'y': 0},
                {'x': size, 'y': 0},
                {'x': size, 'y': size},
                {'x': 0, 'y': size}
            ]
            many_parts.append(part)
        
        # Large container
        large_container = [
            {'x': 0, 'y': 0},
            {'x': 40, 'y': 0},
            {'x': 40, 'y': 30},
            {'x': 0, 'y': 30}
        ]
        
        config = {
            'spacing': 0.5,
            'rotations': 2,  # Fewer rotations for speed
            'population_size': 15,
            'max_generations': 40,
            'mutation_rate': 20
        }
        
        nester = Nester(config)
        nester.add_container(large_container)
        nester.add_parts(many_parts)
        
        result = nester.run()
        
        # Should handle many parts
        self.assertIsNotNone(result)
        self.assertEqual(result['total_parts'], len(many_parts))
        
        # Should achieve reasonable utilization with many small parts
        if result['placed_count'] > 5:  # If we placed a reasonable number
            self.assertGreater(result['utilization'], 0.1)  # At least 10% utilization
    
    def test_edge_cases(self):
        """Test various edge cases"""
        # Test with single part
        single_part_nester = Nester({'max_generations': 5})
        single_part_nester.add_container(self.container_points)
        single_part_nester.add_part(self.parts_data[0])
        
        result = single_part_nester.run()
        self.assertIsNotNone(result)
        self.assertEqual(result['total_parts'], 1)
        
        # Test with part larger than container
        large_part = [
            {'x': 0, 'y': 0},
            {'x': 100, 'y': 0},
            {'x': 100, 'y': 100},
            {'x': 0, 'y': 100}
        ]
        
        large_part_nester = Nester({'max_generations': 5})
        large_part_nester.add_container(self.container_points)
        large_part_nester.add_part(large_part)
        
        result = large_part_nester.run()
        self.assertIsNotNone(result)
        # Large part probably won't fit
        self.assertLessEqual(result['placed_count'], 1)
    
    def test_configuration_validation(self):
        """Test that different configuration parameters work"""
        test_cases = [
            {'curve_tolerance': 0.1},
            {'curve_tolerance': 1.0},
            {'spacing': 0},
            {'spacing': 5},
            {'rotations': 1},
            {'rotations': 16},
            {'population_size': 3},
            {'population_size': 20},
            {'mutation_rate': 1},
            {'mutation_rate': 50},
            {'use_holes': True},
            {'use_holes': False},
            {'explore_concave': True},
            {'explore_concave': False}
        ]
        
        base_config = {
            'max_generations': 5,
            'population_size': 5
        }
        
        for test_config in test_cases:
            with self.subTest(config=test_config):
                config = {**base_config, **test_config}
                
                nester = Nester(config)
                nester.add_container(self.container_points)
                nester.add_parts(self.parts_data[:2])  # Use fewer parts for speed
                
                # Should not crash with any valid configuration
                result = nester.run()
                self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()