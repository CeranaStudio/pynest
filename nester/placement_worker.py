import copy
import math
from .geometry_utils import GeometryUtils
from .nfp_calculator import NFPCalculator


class PlacementWorker:
    """Calculate optimal placement positions using NFP data"""
    
    def __init__(self, container, parts, nfp_cache, config):
        self.container = container
        self.parts = parts
        self.nfp_cache = nfp_cache
        self.config = config
        self.placed_parts = []
    
    def place_parts(self, individual):
        """
        Place parts according to genetic algorithm individual
        
        Returns:
            dict: Result containing fitness and placement data
        """
        self.placed_parts = []
        total_area = 0
        placements = []
        
        # Place parts one by one according to the individual's order
        for i, part_index in enumerate(individual['placement']):
            part = copy.deepcopy(self.parts[part_index])
            rotation = individual['rotation'][i]
            
            # Rotate the part
            if rotation != 0:
                part['points'] = GeometryUtils.rotate_polygon(part['points'], rotation)['points']
            
            # Find best position for this part
            position = self._find_best_position(part, part_index, rotation)
            
            if position is not None:
                # Place the part
                placed_part = {
                    'id': part_index,
                    'x': position['x'],
                    'y': position['y'],
                    'rotation': rotation,
                    'points': GeometryUtils.translate_polygon(part['points'], position['x'], position['y'])
                }
                
                self.placed_parts.append(placed_part)
                placements.append({
                    'p_id': str(part_index),
                    'x': position['x'],
                    'y': position['y'],
                    'rotation': rotation
                })
                
                total_area += part.get('area', GeometryUtils.polygon_area(part['points']))
        
        # Calculate fitness
        container_area = abs(GeometryUtils.polygon_area(self.container['points']))
        utilization = total_area / container_area if container_area > 0 else 0
        
        # Fitness is based on: number of placed parts (higher is better) and utilization
        placed_count = len(self.placed_parts)
        total_parts = len(self.parts)
        
        # Minimize fitness: lower is better
        # Prioritize placing more parts, then maximize utilization
        fitness = (total_parts - placed_count) * 1000 + (1 - utilization) * 100
        
        return {
            'fitness': fitness,
            'placements': [placements],
            'placed_count': placed_count,
            'utilization': utilization
        }
    
    def _find_best_position(self, part, part_id, rotation):
        """Find the best position to place a part"""
        best_position = None
        best_fitness = float('inf')
        
        # Get NFP with container
        container_nfp = self._get_nfp(self.container, part, -1, part_id, True, 0, rotation)
        
        if not container_nfp:
            return None
        
        # Try positions along the NFP boundary
        for nfp_polygon in container_nfp:
            positions = self._generate_candidate_positions(nfp_polygon)
            
            for pos in positions:
                if self._is_valid_position(part, pos, part_id, rotation):
                    fitness = self._evaluate_position(pos)
                    if fitness < best_fitness:
                        best_fitness = fitness
                        best_position = pos
        
        return best_position
    
    def _generate_candidate_positions(self, nfp_polygon):
        """Generate candidate positions along NFP boundary"""
        positions = []
        
        # Add all vertices of the NFP
        for point in nfp_polygon:
            positions.append({'x': point['x'], 'y': point['y']})
        
        # Add points along edges for better coverage
        for i in range(len(nfp_polygon)):
            p1 = nfp_polygon[i]
            p2 = nfp_polygon[(i + 1) % len(nfp_polygon)]
            
            # Add midpoint
            mid_x = (p1['x'] + p2['x']) / 2
            mid_y = (p1['y'] + p2['y']) / 2
            positions.append({'x': mid_x, 'y': mid_y})
        
        return positions
    
    def _is_valid_position(self, part, position, part_id, rotation):
        """Check if a position is valid (no overlaps)"""
        # Translate part to the position
        translated_part = GeometryUtils.translate_polygon(part['points'], position['x'], position['y'])
        
        # Check overlap with already placed parts
        for placed_part in self.placed_parts:
            if self._polygons_overlap(translated_part, placed_part['points']):
                return False
        
        # Check if part is within container bounds
        if not self._part_in_container(translated_part):
            return False
        
        return True
    
    def _polygons_overlap(self, poly1, poly2):
        """Check if two polygons overlap (simplified SAT algorithm)"""
        # Simple bounding box check first
        bounds1 = GeometryUtils.get_polygon_bounds(poly1)
        bounds2 = GeometryUtils.get_polygon_bounds(poly2)
        
        if (bounds1['x'] + bounds1['width'] < bounds2['x'] or
            bounds2['x'] + bounds2['width'] < bounds1['x'] or
            bounds1['y'] + bounds1['height'] < bounds2['y'] or
            bounds2['y'] + bounds2['height'] < bounds1['y']):
            return False
        
        # Check if any vertex of poly1 is inside poly2
        for point in poly1:
            if GeometryUtils.point_in_polygon(point, poly2):
                return True
        
        # Check if any vertex of poly2 is inside poly1
        for point in poly2:
            if GeometryUtils.point_in_polygon(point, poly1):
                return True
        
        return False
    
    def _part_in_container(self, part_points):
        """Check if all points of the part are within the container"""
        for point in part_points:
            if not GeometryUtils.point_in_polygon(point, self.container['points']):
                return False
        return True
    
    def _evaluate_position(self, position):
        """Evaluate the quality of a position (lower is better)"""
        # Simple evaluation: prefer bottom-left positions
        return position['x'] + position['y']
    
    def _get_nfp(self, polygon_a, polygon_b, id_a, id_b, inside, rotation_a, rotation_b):
        """Get NFP from cache or calculate it"""
        cache_key = NFPCalculator.cache_key(id_a, id_b, inside, rotation_a, rotation_b)
        
        if cache_key in self.nfp_cache:
            return self.nfp_cache[cache_key]
        
        # Get configuration parameters
        explore_concave = self.config.get('explore_concave', False)
        use_holes = self.config.get('use_holes', False)
        
        # Calculate NFP with proper configuration
        nfp = NFPCalculator.calculate_nfp(
            polygon_a['points'], 
            polygon_b['points'], 
            inside, 
            explore_concave,
            use_holes
        )
        
        # Cache the result
        self.nfp_cache[cache_key] = nfp
        
        return nfp