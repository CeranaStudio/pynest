import math
import copy
import pyclipper
from .geometry_utils import GeometryUtils


class NFPCalculator:
    """No Fit Polygon calculator using Minkowski difference and other methods"""
    
    @staticmethod
    def calculate_nfp(polygon_a, polygon_b, inside=False, explore_concave=False, use_holes=False):
        """
        Calculate No Fit Polygon between two polygons
        
        Args:
            polygon_a: First polygon (stationary)
            polygon_b: Second polygon (moving)
            inside: If True, calculate inner NFP, otherwise outer NFP
            explore_concave: If True, explore concave areas for better placement
            use_holes: If True, consider holes in polygons
        
        Returns:
            List of NFP polygons
        """
        if inside:
            # For inner NFP (polygon B inside polygon A)
            if GeometryUtils.is_rectangle(polygon_a):
                return NFPCalculator._nfp_rectangle(polygon_a, polygon_b)
            else:
                return NFPCalculator._nfp_polygon_inside(polygon_a, polygon_b, explore_concave)
        else:
            # For outer NFP (polygon B outside polygon A)
            if explore_concave:
                # Use more advanced NFP calculation for concave exploration
                return NFPCalculator._nfp_polygon_orbital(polygon_a, polygon_b)
            else:
                return NFPCalculator._minkowski_difference(polygon_a, polygon_b)

    @staticmethod
    def _nfp_rectangle(rect_polygon, polygon):
        """Calculate NFP for rectangle container"""
        bounds_rect = GeometryUtils.get_polygon_bounds(rect_polygon)
        bounds_poly = GeometryUtils.get_polygon_bounds(polygon)
        
        # NFP for rectangle is simple - it's the rectangle shrunk by the polygon's dimensions
        nfp_width = bounds_rect['width'] - bounds_poly['width']
        nfp_height = bounds_rect['height'] - bounds_poly['height']
        
        if nfp_width <= 0 or nfp_height <= 0:
            return []
        
        # Create the NFP rectangle
        nfp = [
            {'x': bounds_rect['x'], 'y': bounds_rect['y']},
            {'x': bounds_rect['x'] + nfp_width, 'y': bounds_rect['y']},
            {'x': bounds_rect['x'] + nfp_width, 'y': bounds_rect['y'] + nfp_height},
            {'x': bounds_rect['x'], 'y': bounds_rect['y'] + nfp_height}
        ]
        
        return [nfp]

    @staticmethod
    def _nfp_polygon_inside(polygon_a, polygon_b, explore_concave=False):
        """Calculate NFP for irregular polygon container (inner NFP)"""
        if explore_concave:
            # Use more sophisticated orbital method for concave exploration
            return NFPCalculator._nfp_polygon_orbital_inside(polygon_a, polygon_b)
        
        # Simplified implementation using Minkowski sum
        clipper_a = NFPCalculator._to_clipper_coords(polygon_a)
        clipper_b = NFPCalculator._to_clipper_coords(polygon_b)
        
        # Reverse polygon B for Minkowski sum
        clipper_b_reversed = [[-p[0], -p[1]] for p in reversed(clipper_b)]
        
        try:
            # Use Minkowski sum to approximate inner NFP
            pc = pyclipper.Pyclipper()
            pc.AddPath(clipper_a, pyclipper.PT_SUBJECT, True)
            pc.AddPath(clipper_b_reversed, pyclipper.PT_CLIP, True)
            
            solution = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
            
            if solution:
                result = []
                for poly in solution:
                    result.append(NFPCalculator._from_clipper_coords(poly))
                return result
            
        except Exception:
            pass
        
        return []

    @staticmethod
    def _minkowski_difference(polygon_a, polygon_b):
        """Calculate Minkowski difference for outer NFP"""
        # Convert to clipper coordinates
        clipper_a = NFPCalculator._to_clipper_coords(polygon_a)
        clipper_b = NFPCalculator._to_clipper_coords(polygon_b)
        
        # Reverse and negate polygon B for Minkowski difference
        clipper_b_neg = [[-p[0], -p[1]] for p in reversed(clipper_b)]
        
        try:
            # Calculate Minkowski sum (which gives us the difference when B is negated)
            solution = pyclipper.MinkowskiSum(clipper_a, clipper_b_neg, True)
            
            if not solution:
                return []
            
            # Find the largest area polygon (the main NFP)
            largest_area = 0
            largest_poly = None
            
            for poly in solution:
                area = abs(pyclipper.Area(poly))
                if area > largest_area:
                    largest_area = area
                    largest_poly = poly
            
            if largest_poly:
                # Translate by the first point of the original polygon B
                if polygon_b:
                    dx = polygon_b[0]['x']
                    dy = polygon_b[0]['y']
                    
                    translated = []
                    for point in largest_poly:
                        translated.append([
                            point[0] + int(dx * 1000000),
                            point[1] + int(dy * 1000000)
                        ])
                    
                    return [NFPCalculator._from_clipper_coords(translated)]
            
        except Exception:
            pass
        
        return []

    @staticmethod
    def _to_clipper_coords(polygon):
        """Convert polygon to clipper integer coordinates"""
        return [[int(p['x'] * 1000000), int(p['y'] * 1000000)] for p in polygon]

    @staticmethod
    def _from_clipper_coords(clipper_polygon):
        """Convert clipper coordinates back to float"""
        return [{'x': p[0] / 1000000.0, 'y': p[1] / 1000000.0} for p in clipper_polygon]

    @staticmethod
    def _nfp_polygon_orbital(polygon_a, polygon_b):
        """Calculate NFP using orbital method for better concave area exploration"""
        # Simplified orbital calculation that tries to slide polygon B around polygon A
        nfp_points = []
        
        # Get vertices and edge midpoints for better coverage
        slide_points = list(polygon_a)  # All vertices
        
        # Add edge midpoints
        for i in range(len(polygon_a)):
            p1 = polygon_a[i]
            p2 = polygon_a[(i + 1) % len(polygon_a)]
            mid_x = (p1['x'] + p2['x']) / 2
            mid_y = (p1['y'] + p2['y']) / 2
            slide_points.append({'x': mid_x, 'y': mid_y})
        
        # Calculate NFP points by trying to place polygon B at each slide point
        bounds_b = GeometryUtils.get_polygon_bounds(polygon_b)
        
        for slide_point in slide_points:
            # Approximate NFP point (simplified calculation)
            nfp_point = {
                'x': slide_point['x'] - bounds_b['width'] / 2,
                'y': slide_point['y'] - bounds_b['height'] / 2
            }
            
            # Check if this point is not already in the list
            is_duplicate = False
            for existing_point in nfp_points:
                if (abs(existing_point['x'] - nfp_point['x']) < 0.001 and 
                    abs(existing_point['y'] - nfp_point['y']) < 0.001):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                nfp_points.append(nfp_point)
        
        # Sort points to form a proper polygon (clockwise)
        if len(nfp_points) > 2:
            nfp_points = NFPCalculator._sort_points_clockwise(nfp_points)
            return [nfp_points]
        
        return []
    
    @staticmethod
    def _nfp_polygon_orbital_inside(polygon_a, polygon_b):
        """Calculate inner NFP using orbital method for concave exploration"""
        nfp_points = []
        
        # For each edge of polygon A, calculate possible positions
        for i in range(len(polygon_a)):
            p1 = polygon_a[i]
            p2 = polygon_a[(i + 1) % len(polygon_a)]
            
            # Calculate edge vector and normal
            edge_dx = p2['x'] - p1['x']
            edge_dy = p2['y'] - p1['y']
            edge_length = math.sqrt(edge_dx * edge_dx + edge_dy * edge_dy)
            
            if edge_length > 0:
                # Normalize edge vector
                edge_dx /= edge_length
                edge_dy /= edge_length
                
                # Calculate inward normal (perpendicular to edge)
                normal_x = -edge_dy
                normal_y = edge_dx
                
                # Calculate offset distance based on polygon B bounds
                bounds_b = GeometryUtils.get_polygon_bounds(polygon_b)
                max_extent = max(bounds_b['width'], bounds_b['height']) / 2
                
                # Calculate NFP point
                nfp_x = p1['x'] + normal_x * max_extent
                nfp_y = p1['y'] + normal_y * max_extent
                nfp_points.append({'x': nfp_x, 'y': nfp_y})
        
        if len(nfp_points) > 2:
            return [nfp_points]
        
        return []
    
    @staticmethod
    def _sort_points_clockwise(points):
        """Sort points in clockwise order around their centroid"""
        if len(points) < 3:
            return points
        
        # Calculate centroid
        cx = sum(p['x'] for p in points) / len(points)
        cy = sum(p['y'] for p in points) / len(points)
        
        # Sort by angle from centroid
        def angle_from_centroid(point):
            return math.atan2(point['y'] - cy, point['x'] - cx)
        
        return sorted(points, key=angle_from_centroid, reverse=True)  # Clockwise
    
    @staticmethod
    def cache_key(polygon_a_id, polygon_b_id, inside, rotation_a=0, rotation_b=0):
        """Generate cache key for NFP calculation"""
        return f"{polygon_a_id}_{polygon_b_id}_{inside}_{rotation_a}_{rotation_b}"