import unittest
from nester.genetic_algorithm import GeneticAlgorithm


class TestGeneticAlgorithm(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Simple container
        self.container = {
            'points': [
                {'x': 0, 'y': 0},
                {'x': 20, 'y': 0},
                {'x': 20, 'y': 15},
                {'x': 0, 'y': 15}
            ]
        }
        
        # Test parts
        self.parts = [
            {
                'id': 0,
                'points': [
                    {'x': 0, 'y': 0},
                    {'x': 5, 'y': 0},
                    {'x': 5, 'y': 3},
                    {'x': 0, 'y': 3}
                ],
                'area': 15
            },
            {
                'id': 1,
                'points': [
                    {'x': 0, 'y': 0},
                    {'x': 4, 'y': 0},
                    {'x': 4, 'y': 4},
                    {'x': 0, 'y': 4}
                ],
                'area': 16
            },
            {
                'id': 2,
                'points': [
                    {'x': 0, 'y': 0},
                    {'x': 3, 'y': 0},
                    {'x': 3, 'y': 6},
                    {'x': 0, 'y': 6}
                ],
                'area': 18
            }
        ]
        
        # Test configuration
        self.config = {
            'rotations': 4,
            'population_size': 5,
            'mutation_rate': 20
        }
    
    def test_initialization(self):
        """Test genetic algorithm initialization"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Check that population is created
        self.assertEqual(len(ga.population), self.config['population_size'])
        
        # Check that each individual has correct structure
        for individual in ga.population:
            self.assertIn('placement', individual)
            self.assertIn('rotation', individual)
            self.assertIn('fitness', individual)
            
            # Placement should contain all parts
            self.assertEqual(len(individual['placement']), len(self.parts))
            self.assertEqual(len(individual['rotation']), len(self.parts))
            
            # All part indices should be present
            placement_ids = set(individual['placement'])
            expected_ids = set(range(len(self.parts)))
            self.assertEqual(placement_ids, expected_ids)
    
    def test_random_angle_generation(self):
        """Test random angle generation"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Test angle generation for each part
        for i in range(len(self.parts)):
            angle = ga._random_angle(i)
            
            # Angle should be valid (0 <= angle < 360)
            self.assertGreaterEqual(angle, 0)
            self.assertLess(angle, 360)
            
            # Angle should be one of the expected rotation steps
            expected_angles = [j * (360 / self.config['rotations']) for j in range(self.config['rotations'])]
            self.assertIn(angle, expected_angles)
    
    def test_mutation(self):
        """Test individual mutation"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        original = ga.population[0]
        
        # Create multiple mutations to test randomness
        mutations_differ = False
        for _ in range(10):
            mutated = ga._mutate(original)
            
            # Mutated individual should have same structure
            self.assertIn('placement', mutated)
            self.assertIn('rotation', mutated)
            self.assertEqual(len(mutated['placement']), len(original['placement']))
            self.assertEqual(len(mutated['rotation']), len(original['rotation']))
            
            # Should still contain all parts
            placement_ids = set(mutated['placement'])
            expected_ids = set(range(len(self.parts)))
            self.assertEqual(placement_ids, expected_ids)
            
            # Check if mutation occurred
            if (mutated['placement'] != original['placement'] or 
                mutated['rotation'] != original['rotation']):
                mutations_differ = True
        
        # At least some mutations should produce different results
        # (This might occasionally fail due to randomness, but very unlikely)
        self.assertTrue(mutations_differ)
    
    def test_crossover(self):
        """Test crossover operation"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        parent1 = ga.population[0]
        parent2 = ga.population[1]
        
        offspring1, offspring2 = ga._crossover(parent1, parent2)
        
        # Check offspring structure
        for offspring in [offspring1, offspring2]:
            self.assertIn('placement', offspring)
            self.assertIn('rotation', offspring)
            self.assertEqual(len(offspring['placement']), len(self.parts))
            self.assertEqual(len(offspring['rotation']), len(self.parts))
            
            # Should contain all parts exactly once
            placement_ids = set(offspring['placement'])
            expected_ids = set(range(len(self.parts)))
            self.assertEqual(placement_ids, expected_ids)
    
    def test_tournament_selection(self):
        """Test tournament selection"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Set different fitness values
        for i, individual in enumerate(ga.population):
            individual['fitness'] = i * 10  # 0, 10, 20, 30, 40
        
        # Tournament selection should prefer individuals with lower fitness
        selected_fitnesses = []
        for _ in range(20):
            selected = ga._tournament_selection()
            selected_fitnesses.append(selected['fitness'])
        
        # Average selected fitness should be biased toward lower values
        avg_fitness = sum(selected_fitnesses) / len(selected_fitnesses)
        all_fitness_avg = sum(ind['fitness'] for ind in ga.population) / len(ga.population)
        
        # Selected average should be lower than population average
        self.assertLess(avg_fitness, all_fitness_avg)
    
    def test_evolution(self):
        """Test evolution process"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Set initial fitness values
        for i, individual in enumerate(ga.population):
            individual['fitness'] = 100 - i  # 100, 99, 98, 97, 96
        
        initial_best_fitness = ga.get_best()['fitness']
        initial_generation = ga.generation_count
        
        # Evolve one generation
        ga.evolve()
        
        # Check that generation count increased
        self.assertEqual(ga.generation_count, initial_generation + 1)
        
        # Population size should remain the same
        self.assertEqual(len(ga.population), self.config['population_size'])
        
        # All individuals should have valid structure
        for individual in ga.population:
            self.assertIn('placement', individual)
            self.assertIn('rotation', individual)
            self.assertEqual(len(individual['placement']), len(self.parts))
    
    def test_get_best(self):
        """Test getting best individual"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Set fitness values
        fitnesses = [50, 10, 30, 20, 40]
        for i, individual in enumerate(ga.population):
            individual['fitness'] = fitnesses[i]
        
        best = ga.get_best()
        self.assertEqual(best['fitness'], 10)  # Lowest fitness
    
    def test_get_statistics(self):
        """Test statistics generation"""
        ga = GeneticAlgorithm(self.parts, self.container, self.config)
        
        # Set fitness values
        fitnesses = [50, 10, 30, 20, 40]
        for i, individual in enumerate(ga.population):
            individual['fitness'] = fitnesses[i]
        
        stats = ga.get_statistics()
        
        self.assertIn('generation', stats)
        self.assertIn('best_fitness', stats)
        self.assertIn('worst_fitness', stats)
        self.assertIn('avg_fitness', stats)
        
        self.assertEqual(stats['best_fitness'], 10)
        self.assertEqual(stats['worst_fitness'], 50)
        self.assertEqual(stats['avg_fitness'], 30)
    
    def test_config_variations(self):
        """Test with different configurations"""
        # Test with different rotation counts
        config_8_rot = self.config.copy()
        config_8_rot['rotations'] = 8
        
        ga = GeneticAlgorithm(self.parts, self.container, config_8_rot)
        angle = ga._random_angle(0)
        
        # Should be multiple of 45 degrees (360/8)
        self.assertEqual(angle % 45, 0)
        
        # Test with different population size
        config_large_pop = self.config.copy()
        config_large_pop['population_size'] = 10
        
        ga = GeneticAlgorithm(self.parts, self.container, config_large_pop)
        self.assertEqual(len(ga.population), 10)


if __name__ == '__main__':
    unittest.main()