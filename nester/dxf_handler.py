import ezdxf
import math
from ezdxf import units
from .geometry_utils import GeometryUtils


class DXFHandler:
    """Handle DXF file input and output for nesting"""
    
    @staticmethod
    def read_dxf(file_path):
        """
        Read DXF file and extract polygon shapes
        
        Args:
            file_path (str): Path to DXF file
            
        Returns:
            list: List of polygons, each containing points
        """
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            polygons = []
            
            # Process different entity types
            for entity in msp:
                points = DXFHandler._extract_points_from_entity(entity)
                if points and len(points) >= 3:
                    # Ensure polygon is closed
                    if not DXFHandler._points_equal(points[0], points[-1]):
                        points.append(points[0])
                    polygons.append(points[:-1])  # Remove duplicate closing point
            
            return polygons
            
        except Exception as e:
            raise ValueError(f"Error reading DXF file: {str(e)}")
    
    @staticmethod
    def _extract_points_from_entity(entity):
        """Extract points from different DXF entity types"""
        points = []
        
        if entity.dxftype() == 'LWPOLYLINE':
            # Lightweight polyline
            for point in entity.get_points('xy'):
                points.append({'x': float(point[0]), 'y': float(point[1])})
                
        elif entity.dxftype() == 'POLYLINE':
            # Regular polyline
            for vertex in entity.vertices:
                points.append({'x': float(vertex.dxf.location.x), 'y': float(vertex.dxf.location.y)})
                
        elif entity.dxftype() == 'LINE':
            # Line segment
            start = entity.dxf.start
            end = entity.dxf.end
            points.append({'x': float(start.x), 'y': float(start.y)})
            points.append({'x': float(end.x), 'y': float(end.y)})
            
        elif entity.dxftype() == 'CIRCLE':
            # Convert circle to polygon
            center = entity.dxf.center
            radius = entity.dxf.radius
            points = DXFHandler._circle_to_polygon(
                {'x': float(center.x), 'y': float(center.y)}, 
                float(radius), 
                32  # number of segments
            )
            
        elif entity.dxftype() == 'ARC':
            # Convert arc to polyline
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            points = DXFHandler._arc_to_polygon(
                {'x': float(center.x), 'y': float(center.y)},
                float(radius),
                start_angle,
                end_angle,
                16  # number of segments
            )
            
        elif entity.dxftype() == 'SPLINE':
            # Convert spline to polyline approximation
            try:
                # Sample points along the spline
                points = []
                for t in [i / 20.0 for i in range(21)]:  # 21 points
                    point = entity.point(t)
                    points.append({'x': float(point.x), 'y': float(point.y)})
            except:
                points = []
        
        return points
    
    @staticmethod
    def _circle_to_polygon(center, radius, segments):
        """Convert circle to polygon"""
        points = []
        angle_step = 2 * math.pi / segments
        
        for i in range(segments):
            angle = i * angle_step
            x = center['x'] + radius * math.cos(angle)
            y = center['y'] + radius * math.sin(angle)
            points.append({'x': x, 'y': y})
        
        return points
    
    @staticmethod
    def _arc_to_polygon(center, radius, start_angle, end_angle, segments):
        """Convert arc to polygon"""
        points = []
        
        # Normalize angles
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        angle_range = end_angle - start_angle
        angle_step = angle_range / segments
        
        for i in range(segments + 1):
            angle = start_angle + i * angle_step
            x = center['x'] + radius * math.cos(angle)
            y = center['y'] + radius * math.sin(angle)
            points.append({'x': x, 'y': y})
        
        return points
    
    @staticmethod
    def _points_equal(p1, p2, tolerance=1e-6):
        """Check if two points are equal within tolerance"""
        return (abs(p1['x'] - p2['x']) < tolerance and 
                abs(p1['y'] - p2['y']) < tolerance)
    
    @staticmethod
    def write_dxf(file_path, placement_data):
        """
        Write nesting result to DXF file
        
        Args:
            file_path (str): Output DXF file path
            placement_data (list): Placement data from nester
        """
        # Create new DXF document
        doc = ezdxf.new('R2010')  # DXF R2010 = AutoCAD 2010
        doc.units = units.MM  # Set units to millimeters
        
        msp = doc.modelspace()
        
        # Create layers
        doc.layers.new('CONTAINER', dxfattribs={'color': 1})  # Red for container
        doc.layers.new('PARTS', dxfattribs={'color': 2})      # Yellow for parts
        
        for bin_index, bin_data in enumerate(placement_data):
            # Add container outline
            container_points = bin_data['container']['points']
            container_coords = [(p['x'], p['y']) for p in container_points]
            container_coords.append(container_coords[0])  # Close the polygon
            
            msp.add_lwpolyline(
                container_coords,
                dxfattribs={'layer': 'CONTAINER'}
            )
            
            # Add parts
            for part in bin_data['parts']:
                part_points = part['placed_points']
                part_coords = [(p['x'], p['y']) for p in part_points]
                part_coords.append(part_coords[0])  # Close the polygon
                
                msp.add_lwpolyline(
                    part_coords,
                    dxfattribs={'layer': 'PARTS'}
                )
            
            # If multiple bins, offset them horizontally
            if bin_index < len(placement_data) - 1:
                container_bounds = GeometryUtils.get_polygon_bounds(container_points)
                offset_x = container_bounds['width'] + 50  # 50 unit spacing
                
                # Offset all entities for next bin
                for entity in msp:
                    if hasattr(entity, 'translate'):
                        entity.translate(offset_x, 0, 0)
        
        # Save the DXF file
        doc.saveas(file_path)
    
    @staticmethod
    def read_multiple_dxf_files(file_paths):
        """
        Read multiple DXF files and return all polygons
        
        Args:
            file_paths (list): List of DXF file paths
            
        Returns:
            list: All polygons from all files
        """
        all_polygons = []
        
        for file_path in file_paths:
            try:
                polygons = DXFHandler.read_dxf(file_path)
                all_polygons.extend(polygons)
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {str(e)}")
        
        return all_polygons
    
    @staticmethod
    def get_dxf_info(file_path):
        """
        Get information about a DXF file
        
        Args:
            file_path (str): Path to DXF file
            
        Returns:
            dict: Information about the DXF file
        """
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            entity_count = {}
            total_entities = 0
            
            for entity in msp:
                entity_type = entity.dxftype()
                entity_count[entity_type] = entity_count.get(entity_type, 0) + 1
                total_entities += 1
            
            return {
                'version': doc.dxfversion,
                'units': doc.units,
                'total_entities': total_entities,
                'entity_types': entity_count
            }
            
        except Exception as e:
            return {'error': str(e)}