import copy
import math
from .geometry_utils import GeometryUtils
from .genetic_algorithm import GeneticAlgorithm
from .placement_worker import PlacementWorker


class Nester:
    """Main nesting class that coordinates the nesting algorithm"""
    
    def __init__(self, config=None):
        """
        Initialize the nester with configuration
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = {
            'curve_tolerance': 0.3,    # Maximum error allowed for curve approximation
            'spacing': 0,              # Minimum space between parts (laser kerf, CNC offset etc.)
            'rotations': 4,            # Number of rotation angles to evaluate for each part
            'population_size': 10,     # Population size for the Genetic Algorithm
            'mutation_rate': 10,       # Mutation rate percentage (1-50)
            'max_generations': 100,    # Maximum number of generations
            'use_holes': False,        # Enable part-in-part placement
            'explore_concave': False   # Explore concave areas for better placement
        }
        
        if config:
            self.config.update(config)
        
        self.container = None
        self.parts = []
        self.nfp_cache = {}
        self.best_result = None
        self.ga = None
    
    def add_container(self, points):
        """
        Add container polygon
        
        Args:
            points: List of points defining the container polygon
                   Format: [{'x': float, 'y': float}, ...]
        """
        if not points or len(points) < 3:
            raise ValueError("Container must have at least 3 points")
        
        # Normalize and clean the container
        normalized_points = GeometryUtils.normalize_polygon(points)
        bounds = GeometryUtils.get_polygon_bounds(normalized_points)
        
        self.container = {
            'id': -1,
            'points': normalized_points,
            'area': abs(GeometryUtils.polygon_area(normalized_points)),
            'width': bounds['width'],
            'height': bounds['height']
        }
        
        # Apply spacing offset if configured
        if self.config['spacing'] > 0:
            offset_points = GeometryUtils.polygon_offset(
                self.container['points'], 
                -self.config['spacing'] / 2,
                self.config['curve_tolerance']
            )
            if offset_points:
                self.container['points'] = offset_points
                new_bounds = GeometryUtils.get_polygon_bounds(offset_points)
                self.container['width'] = new_bounds['width']
                self.container['height'] = new_bounds['height']
    
    def add_part(self, points, part_id=None):
        """
        Add a part to be nested
        
        Args:
            points: List of points defining the part polygon
            part_id: Optional ID for the part
        """
        if not points or len(points) < 3:
            raise ValueError("Part must have at least 3 points")
        
        # Normalize the part
        normalized_points = GeometryUtils.normalize_polygon(points)
        
        # Apply spacing offset
        if self.config['spacing'] > 0:
            offset_points = GeometryUtils.polygon_offset(
                normalized_points, 
                self.config['spacing'] / 2,
                self.config['curve_tolerance']
            )
            if offset_points:
                normalized_points = offset_points
        
        part = {
            'id': len(self.parts) if part_id is None else part_id,
            'points': normalized_points,
            'area': abs(GeometryUtils.polygon_area(normalized_points))
        }
        
        self.parts.append(part)
    
    def add_parts(self, parts_list):
        """
        Add multiple parts at once
        
        Args:
            parts_list: List of point lists or dict with 'points' key
        """
        for i, part_data in enumerate(parts_list):
            if isinstance(part_data, dict) and 'points' in part_data:
                points = part_data['points']
                part_id = part_data.get('id', len(self.parts))
            else:
                points = part_data
                part_id = len(self.parts)
            
            self.add_part(points, part_id)
    
    def clear_parts(self):
        """Clear all parts"""
        self.parts = []
        self.nfp_cache = {}
        self.best_result = None
        self.ga = None
    
    def run(self, max_generations=None, progress_callback=None):
        """
        Run the nesting algorithm
        
        Args:
            max_generations: Maximum number of generations to run
            progress_callback: Optional callback function for progress updates
        
        Returns:
            dict: Best nesting result
        """
        if not self.container:
            raise ValueError("No container defined")
        
        if not self.parts:
            raise ValueError("No parts to nest")
        
        max_gen = max_generations or self.config['max_generations']
        
        # Sort parts by area (largest first)
        sorted_parts = sorted(self.parts, key=lambda p: p['area'], reverse=True)
        
        # Initialize genetic algorithm
        if not self.ga:
            self.ga = GeneticAlgorithm(sorted_parts, self.container, self.config)
        
        # Run genetic algorithm
        for generation in range(max_gen):
            # Evaluate fitness for all individuals
            for individual in self.ga.population:
                if individual['fitness'] == float('inf'):
                    worker = PlacementWorker(self.container, sorted_parts, self.nfp_cache, self.config)
                    result = worker.place_parts(individual)
                    individual['fitness'] = result['fitness']
                    individual['result'] = result
            
            # Update best result
            current_best = self.ga.get_best()
            if self.best_result is None or current_best['fitness'] < self.best_result['fitness']:
                self.best_result = copy.deepcopy(current_best)
            
            # Progress callback
            if progress_callback:
                stats = self.ga.get_statistics()
                stats['best_placed'] = current_best.get('result', {}).get('placed_count', 0)
                stats['total_parts'] = len(sorted_parts)
                progress_callback(stats)
            
            # Evolve to next generation
            if generation < max_gen - 1:
                self.ga.evolve()
            
            # Early termination if all parts are placed
            if current_best.get('result', {}).get('placed_count', 0) == len(sorted_parts):
                break
        
        return self.get_best_result()
    
    def get_best_result(self):
        """Get the best nesting result"""
        if not self.best_result:
            return None
        
        result = self.best_result.get('result', {})
        
        return {
            'fitness': self.best_result['fitness'],
            'placements': result.get('placements', []),
            'placed_count': result.get('placed_count', 0),
            'total_parts': len(self.parts),
            'utilization': result.get('utilization', 0),
            'container': self.container,
            'parts': self.parts
        }
    
    def get_placement_data(self):
        """Get detailed placement data for visualization"""
        result = self.get_best_result()
        if not result:
            return None
        
        placement_data = []
        
        for bin_placements in result['placements']:
            bin_data = {
                'container': self.container,
                'parts': []
            }
            
            for placement in bin_placements:
                part_id = int(placement['p_id'])
                part = self.parts[part_id]
                
                # Get rotated and translated points
                points = part['points']
                if placement['rotation'] != 0:
                    rotated = GeometryUtils.rotate_polygon(points, placement['rotation'])
                    points = rotated['points']
                
                translated_points = GeometryUtils.translate_polygon(
                    points, placement['x'], placement['y']
                )
                
                bin_data['parts'].append({
                    'id': part_id,
                    'original_points': part['points'],
                    'placed_points': translated_points,
                    'x': placement['x'],
                    'y': placement['y'],
                    'rotation': placement['rotation']
                })
            
            placement_data.append(bin_data)
        
        return placement_data