import unittest
from nester import Nester


class TestNester(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Simple container
        self.container_points = [
            {'x': 0, 'y': 0},
            {'x': 20, 'y': 0},
            {'x': 20, 'y': 15},
            {'x': 0, 'y': 15}
        ]
        
        # Test parts
        self.parts_data = [
            [
                {'x': 0, 'y': 0},
                {'x': 5, 'y': 0},
                {'x': 5, 'y': 3},
                {'x': 0, 'y': 3}
            ],
            [
                {'x': 0, 'y': 0},
                {'x': 4, 'y': 0},
                {'x': 4, 'y': 4},
                {'x': 0, 'y': 4}
            ],
            [
                {'x': 0, 'y': 0},
                {'x': 3, 'y': 0},
                {'x': 3, 'y': 2},
                {'x': 0, 'y': 2}
            ]
        ]
        
        # Test configuration
        self.config = {
            'spacing': 1,
            'rotations': 4,
            'population_size': 5,
            'mutation_rate': 20,
            'max_generations': 10
        }
    
    def test_initialization(self):
        """Test nester initialization"""
        nester = Nester()
        
        # Check default configuration
        self.assertIn('spacing', nester.config)
        self.assertIn('rotations', nester.config)
        self.assertIn('population_size', nester.config)
        
        # Test with custom config
        nester_custom = Nester(self.config)
        self.assertEqual(nester_custom.config['spacing'], self.config['spacing'])
        self.assertEqual(nester_custom.config['rotations'], self.config['rotations'])
    
    def test_add_container(self):
        """Test adding container"""
        nester = Nester(self.config)
        nester.add_container(self.container_points)
        
        # Check container was added
        self.assertIsNotNone(nester.container)
        self.assertEqual(nester.container['id'], -1)
        self.assertIn('points', nester.container)
        self.assertIn('area', nester.container)
        self.assertIn('width', nester.container)
        self.assertIn('height', nester.container)
        
        # Container should have valid dimensions
        self.assertGreater(nester.container['area'], 0)
        self.assertGreater(nester.container['width'], 0)
        self.assertGreater(nester.container['height'], 0)
    
    def test_add_part(self):
        """Test adding individual parts"""
        nester = Nester(self.config)
        
        # Add first part
        nester.add_part(self.parts_data[0])
        self.assertEqual(len(nester.parts), 1)
        
        # Check part structure
        part = nester.parts[0]
        self.assertIn('id', part)
        self.assertIn('points', part)
        self.assertIn('area', part)
        self.assertGreater(part['area'], 0)
        
        # Add second part with custom ID
        nester.add_part(self.parts_data[1], part_id='custom_id')
        self.assertEqual(len(nester.parts), 2)
        self.assertEqual(nester.parts[1]['id'], 'custom_id')
    
    def test_add_parts(self):
        """Test adding multiple parts"""
        nester = Nester(self.config)
        nester.add_parts(self.parts_data)
        
        self.assertEqual(len(nester.parts), len(self.parts_data))
        
        # All parts should have valid structure
        for part in nester.parts:
            self.assertIn('id', part)
            self.assertIn('points', part)
            self.assertIn('area', part)
            self.assertGreater(part['area'], 0)
    
    def test_add_parts_with_dict_format(self):
        """Test adding parts in dictionary format"""
        nester = Nester(self.config)
        
        dict_parts = [
            {'points': self.parts_data[0], 'id': 'part1'},
            {'points': self.parts_data[1], 'id': 'part2'}
        ]
        
        nester.add_parts(dict_parts)
        
        self.assertEqual(len(nester.parts), 2)
        self.assertEqual(nester.parts[0]['id'], 'part1')
        self.assertEqual(nester.parts[1]['id'], 'part2')
    
    def test_clear_parts(self):
        """Test clearing parts"""
        nester = Nester(self.config)
        nester.add_parts(self.parts_data)
        
        self.assertEqual(len(nester.parts), len(self.parts_data))
        
        nester.clear_parts()
        
        self.assertEqual(len(nester.parts), 0)
        self.assertEqual(len(nester.nfp_cache), 0)
        self.assertIsNone(nester.best_result)
        self.assertIsNone(nester.ga)
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs"""
        nester = Nester()
        
        # Invalid container (too few points)
        with self.assertRaises(ValueError):
            nester.add_container([{'x': 0, 'y': 0}, {'x': 1, 'y': 1}])
        
        # Invalid part (too few points)
        with self.assertRaises(ValueError):
            nester.add_part([{'x': 0, 'y': 0}, {'x': 1, 'y': 1}])
        
        # Running without container
        with self.assertRaises(ValueError):
            nester.run()
        
        # Running without parts
        nester.add_container(self.container_points)
        with self.assertRaises(ValueError):
            nester.run()
    
    def test_run_nesting(self):
        """Test running the nesting algorithm"""
        nester = Nester(self.config)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        # Run nesting
        result = nester.run()
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertIn('fitness', result)
        self.assertIn('placements', result)
        self.assertIn('placed_count', result)
        self.assertIn('total_parts', result)
        self.assertIn('utilization', result)
        self.assertIn('container', result)
        self.assertIn('parts', result)
        
        # Check values are reasonable
        self.assertGreaterEqual(result['placed_count'], 0)
        self.assertEqual(result['total_parts'], len(self.parts_data))
        self.assertGreaterEqual(result['utilization'], 0)
        self.assertLessEqual(result['utilization'], 1)
    
    def test_run_with_progress_callback(self):
        """Test running with progress callback"""
        nester = Nester(self.config)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        progress_calls = []
        
        def progress_callback(stats):
            progress_calls.append(stats)
            self.assertIn('generation', stats)
            self.assertIn('best_fitness', stats)
            self.assertIn('best_placed', stats)
            self.assertIn('total_parts', stats)
        
        result = nester.run(progress_callback=progress_callback)
        
        # Progress callback should have been called
        self.assertGreater(len(progress_calls), 0)
        
        # Check that generations progressed
        if len(progress_calls) > 1:
            self.assertGreater(progress_calls[-1]['generation'], progress_calls[0]['generation'])
    
    def test_get_placement_data(self):
        """Test getting detailed placement data"""
        nester = Nester(self.config)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        result = nester.run()
        placement_data = nester.get_placement_data()
        
        if result['placed_count'] > 0:
            self.assertIsNotNone(placement_data)
            self.assertIsInstance(placement_data, list)
            
            # Check structure of placement data
            for bin_data in placement_data:
                self.assertIn('container', bin_data)
                self.assertIn('parts', bin_data)
                
                # Check placed parts
                for part in bin_data['parts']:
                    self.assertIn('id', part)
                    self.assertIn('original_points', part)
                    self.assertIn('placed_points', part)
                    self.assertIn('x', part)
                    self.assertIn('y', part)
                    self.assertIn('rotation', part)
    
    def test_spacing_configuration(self):
        """Test spacing configuration"""
        config_with_spacing = self.config.copy()
        config_with_spacing['spacing'] = 2
        
        nester = Nester(config_with_spacing)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        # Container should be reduced by spacing
        original_area = 20 * 15  # 300
        self.assertLess(nester.container['area'], original_area)
    
    def test_different_configurations(self):
        """Test with different configuration parameters"""
        # Test with more rotations
        config_more_rot = self.config.copy()
        config_more_rot['rotations'] = 8
        
        nester = Nester(config_more_rot)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        result = nester.run(max_generations=5)
        self.assertIsNotNone(result)
        
        # Test with larger population
        config_large_pop = self.config.copy()
        config_large_pop['population_size'] = 15
        
        nester = Nester(config_large_pop)
        nester.add_container(self.container_points)
        nester.add_parts(self.parts_data)
        
        result = nester.run(max_generations=5)
        self.assertIsNotNone(result)
    
    def test_get_best_result_without_run(self):
        """Test getting best result before running"""
        nester = Nester()
        result = nester.get_best_result()
        self.assertIsNone(result)
        
        placement_data = nester.get_placement_data()
        self.assertIsNone(placement_data)


if __name__ == '__main__':
    unittest.main()