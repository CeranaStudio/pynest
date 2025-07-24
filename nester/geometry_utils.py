import math
import copy
import pyclipper

TOL = 1e-7


class GeometryUtils:
    @staticmethod
    def almost_equal(a, b, tolerance=TOL):
        """Check if two values are approximately equal"""
        return abs(a - b) < tolerance

    @staticmethod
    def polygon_area(polygon):
        """Calculate the area of a polygon using the shoelace formula"""
        area = 0.0
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i]['x'] * polygon[j]['y']
            area -= polygon[j]['x'] * polygon[i]['y']
        return area / 2.0

    @staticmethod
    def get_polygon_bounds(polygon):
        """Get the bounding box of a polygon"""
        if not polygon:
            return None
        
        min_x = max_x = polygon[0]['x']
        min_y = max_y = polygon[0]['y']
        
        for point in polygon:
            min_x = min(min_x, point['x'])
            max_x = max(max_x, point['x'])
            min_y = min(min_y, point['y'])
            max_y = max(max_y, point['y'])
        
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }

    @staticmethod
    def rotate_polygon(polygon, angle_degrees):
        """Rotate a polygon by the given angle in degrees"""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotated_points = []
        for point in polygon:
            x = point['x'] * cos_a - point['y'] * sin_a
            y = point['x'] * sin_a + point['y'] * cos_a
            rotated_points.append({'x': x, 'y': y})
        
        return {
            'points': rotated_points,
            'width': GeometryUtils.get_polygon_bounds(rotated_points)['width'],
            'height': GeometryUtils.get_polygon_bounds(rotated_points)['height']
        }

    @staticmethod
    def translate_polygon(polygon, dx, dy):
        """Translate a polygon by the given offset"""
        translated = []
        for point in polygon:
            translated.append({
                'x': point['x'] + dx,
                'y': point['y'] + dy
            })
        return translated

    @staticmethod
    def normalize_polygon(polygon):
        """Normalize polygon to origin and ensure counterclockwise orientation"""
        if not polygon:
            return polygon
        
        # Move to origin
        bounds = GeometryUtils.get_polygon_bounds(polygon)
        normalized = []
        for point in polygon:
            normalized.append({
                'x': point['x'] - bounds['x'],
                'y': point['y'] - bounds['y']
            })
        
        # Ensure counterclockwise orientation
        area = GeometryUtils.polygon_area(normalized)
        if area > 0:
            normalized.reverse()
        
        return normalized

    @staticmethod
    def polygon_offset(polygon, offset, curve_tolerance=0.3):
        """Offset a polygon by the given distance"""
        if not polygon or offset == 0:
            return polygon
        
        # Convert to clipper format
        clipper_polygon = [[int(p['x'] * 1000000), int(p['y'] * 1000000)] for p in polygon]
        
        # Use curve tolerance for offsetting (miter limit = 2 is standard)
        miter_limit = 2
        co = pyclipper.PyclipperOffset(miter_limit, curve_tolerance)
        co.AddPath(clipper_polygon, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        
        offset_clipper = int(offset * 1000000)
        result = co.Execute(offset_clipper)
        
        if not result:
            return []
        
        # Convert back
        result_polygon = []
        for point in result[0]:
            result_polygon.append({
                'x': point[0] / 1000000.0,
                'y': point[1] / 1000000.0
            })
        
        return result_polygon

    @staticmethod
    def point_in_polygon(point, polygon):
        """Check if a point is inside a polygon using ray casting"""
        x, y = point['x'], point['y']
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]['x'], polygon[0]['y']
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]['x'], polygon[i % n]['y']
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    @staticmethod
    def is_rectangle(polygon, tolerance=TOL):
        """Check if a polygon is a rectangle"""
        if len(polygon) != 4:
            return False
        
        bounds = GeometryUtils.get_polygon_bounds(polygon)
        
        for point in polygon:
            x_on_edge = (GeometryUtils.almost_equal(point['x'], bounds['x'], tolerance) or 
                        GeometryUtils.almost_equal(point['x'], bounds['x'] + bounds['width'], tolerance))
            y_on_edge = (GeometryUtils.almost_equal(point['y'], bounds['y'], tolerance) or 
                        GeometryUtils.almost_equal(point['y'], bounds['y'] + bounds['height'], tolerance))
            
            if not (x_on_edge and y_on_edge):
                return False
        
        return True