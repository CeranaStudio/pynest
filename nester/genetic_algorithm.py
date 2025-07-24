import random
import copy
from .geometry_utils import GeometryUtils


class GeneticAlgorithm:
    """Genetic Algorithm for optimizing part placement"""
    
    def __init__(self, parts, container, config):
        self.parts = parts
        self.container = container
        self.config = config
        self.population = []
        self.generation_count = 0
        
        # Initialize population
        self._initialize_population()
    
    def _initialize_population(self):
        """Create initial population"""
        # Create initial individual with parts in order
        initial_placement = list(range(len(self.parts)))
        initial_rotations = [self._random_angle(i) for i in range(len(self.parts))]
        
        initial_individual = {
            'placement': initial_placement,
            'rotation': initial_rotations,
            'fitness': float('inf')
        }
        
        self.population = [initial_individual]
        
        # Create mutated individuals to fill population
        for _ in range(1, self.config['population_size']):
            mutant = self._mutate(copy.deepcopy(initial_individual))
            self.population.append(mutant)
    
    def _random_angle(self, part_index):
        """Generate a random valid rotation angle for a part"""
        angles = []
        for i in range(self.config['rotations']):
            angle = i * (360 / self.config['rotations'])
            angles.append(angle)
        
        # Filter angles that fit within container bounds
        valid_angles = []
        part = self.parts[part_index]
        
        for angle in angles:
            rotated = GeometryUtils.rotate_polygon(part['points'], angle)
            container_bounds = GeometryUtils.get_polygon_bounds(self.container['points'])
            
            if (rotated['width'] <= container_bounds['width'] and 
                rotated['height'] <= container_bounds['height']):
                valid_angles.append(angle)
        
        return random.choice(valid_angles) if valid_angles else 0
    
    def _mutate(self, individual):
        """Mutate an individual"""
        mutant = copy.deepcopy(individual)
        
        # Swap mutation - swap two parts in placement order
        if random.random() < self.config['mutation_rate'] / 100.0:
            if len(mutant['placement']) > 1:
                i = random.randint(0, len(mutant['placement']) - 1)
                j = random.randint(0, len(mutant['placement']) - 1)
                mutant['placement'][i], mutant['placement'][j] = mutant['placement'][j], mutant['placement'][i]
        
        # Rotation mutation - change rotation of a random part
        if random.random() < self.config['mutation_rate'] / 100.0:
            i = random.randint(0, len(mutant['rotation']) - 1)
            mutant['rotation'][i] = self._random_angle(mutant['placement'][i])
        
        return mutant
    
    def _crossover(self, parent1, parent2):
        """Create two offspring from two parents using order crossover"""
        length = len(parent1['placement'])
        
        # Select crossover points
        start = random.randint(0, length - 1)
        end = random.randint(start, length - 1)
        
        # Create offspring
        offspring1 = {'placement': [-1] * length, 'rotation': [0] * length, 'fitness': float('inf')}
        offspring2 = {'placement': [-1] * length, 'rotation': [0] * length, 'fitness': float('inf')}
        
        # Copy segment from parent1 to offspring1
        for i in range(start, end + 1):
            offspring1['placement'][i] = parent1['placement'][i]
            offspring1['rotation'][i] = parent1['rotation'][i]
        
        # Copy segment from parent2 to offspring2
        for i in range(start, end + 1):
            offspring2['placement'][i] = parent2['placement'][i]
            offspring2['rotation'][i] = parent2['rotation'][i]
        
        # Fill remaining positions
        self._fill_offspring(offspring1, parent2, start, end)
        self._fill_offspring(offspring2, parent1, start, end)
        
        return offspring1, offspring2
    
    def _fill_offspring(self, offspring, parent, start, end):
        """Fill remaining positions in offspring from parent"""
        used = set(offspring['placement'][start:end+1])
        
        parent_index = 0
        for i in range(len(offspring['placement'])):
            if offspring['placement'][i] == -1:
                # Find next unused element from parent
                while parent['placement'][parent_index] in used:
                    parent_index += 1
                
                offspring['placement'][i] = parent['placement'][parent_index]
                offspring['rotation'][i] = parent['rotation'][parent_index]
                used.add(parent['placement'][parent_index])
                parent_index += 1
    
    def _tournament_selection(self, tournament_size=3):
        """Select individual using tournament selection"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return min(tournament, key=lambda x: x['fitness'])
    
    def evolve(self):
        """Run one generation of the genetic algorithm"""
        # Sort population by fitness
        self.population.sort(key=lambda x: x['fitness'])
        
        new_population = []
        
        # Elitism - keep best individual
        new_population.append(copy.deepcopy(self.population[0]))
        
        # Generate rest of population
        while len(new_population) < self.config['population_size']:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if random.random() < 0.8:  # Crossover probability
                offspring1, offspring2 = self._crossover(parent1, parent2)
            else:
                offspring1 = copy.deepcopy(parent1)
                offspring2 = copy.deepcopy(parent2)
            
            # Mutation
            offspring1 = self._mutate(offspring1)
            offspring2 = self._mutate(offspring2)
            
            new_population.append(offspring1)
            if len(new_population) < self.config['population_size']:
                new_population.append(offspring2)
        
        self.population = new_population
        self.generation_count += 1
    
    def get_best(self):
        """Get the best individual from current population"""
        return min(self.population, key=lambda x: x['fitness'])
    
    def get_statistics(self):
        """Get statistics about current population"""
        fitnesses = [ind['fitness'] for ind in self.population]
        return {
            'generation': self.generation_count,
            'best_fitness': min(fitnesses),
            'worst_fitness': max(fitnesses),
            'avg_fitness': sum(fitnesses) / len(fitnesses)
        }