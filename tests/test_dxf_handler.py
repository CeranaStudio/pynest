import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from nester.dxf_handler import DXFHandler


class TestDXFHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Sample polygon data
        self.sample_polygons = [
            [
                {'x': 0, 'y': 0},
                {'x': 10, 'y': 0},
                {'x': 10, 'y': 5},
                {'x': 0, 'y': 5}
            ],
            [
                {'x': 0, 'y': 0},
                {'x': 6, 'y': 0},
                {'x': 3, 'y': 4}
            ]
        ]
        
        # Sample placement data
        self.placement_data = [
            {
                'container': {
                    'points': [
                        {'x': 0, 'y': 0},
                        {'x': 20, 'y': 0},
                        {'x': 20, 'y': 15},
                        {'x': 0, 'y': 15}
                    ]
                },
                'parts': [
                    {
                        'id': 0,
                        'placed_points': [
                            {'x': 2, 'y': 2},
                            {'x': 7, 'y': 2},
                            {'x': 7, 'y': 5},
                            {'x': 2, 'y': 5}
                        ],
                        'x': 2,
                        'y': 2,
                        'rotation': 0
                    },
                    {
                        'id': 1,
                        'placed_points': [
                            {'x': 10, 'y': 3},
                            {'x': 13, 'y': 3},
                            {'x': 11.5, 'y': 7}
                        ],
                        'x': 10,
                        'y': 3,
                        'rotation': 0
                    }
                ]
            }
        ]
    
    def test_points_equal(self):
        """Test point equality checking"""
        p1 = {'x': 1.0, 'y': 2.0}
        p2 = {'x': 1.0, 'y': 2.0}
        p3 = {'x': 1.1, 'y': 2.0}
        
        self.assertTrue(DXFHandler._points_equal(p1, p2))
        self.assertFalse(DXFHandler._points_equal(p1, p3))
        
        # Test with tolerance
        p4 = {'x': 1.0000001, 'y': 2.0}
        self.assertTrue(DXFHandler._points_equal(p1, p4))
    
    def test_circle_to_polygon(self):
        """Test circle to polygon conversion"""
        center = {'x': 5, 'y': 5}
        radius = 3
        segments = 8
        
        polygon = DXFHandler._circle_to_polygon(center, radius, segments)
        
        # Should have correct number of points
        self.assertEqual(len(polygon), segments)
        
        # All points should be approximately at the correct radius
        for point in polygon:
            distance = ((point['x'] - center['x'])**2 + (point['y'] - center['y'])**2)**0.5
            self.assertAlmostEqual(distance, radius, places=5)
    
    def test_arc_to_polygon(self):
        """Test arc to polygon conversion"""
        center = {'x': 0, 'y': 0}
        radius = 5
        start_angle = 0  # 0 degrees
        end_angle = 1.5708  # 90 degrees (π/2)
        segments = 4
        
        polygon = DXFHandler._arc_to_polygon(center, radius, start_angle, end_angle, segments)
        
        # Should have segments + 1 points (including both endpoints)
        self.assertEqual(len(polygon), segments + 1)
        
        # First point should be at start angle
        first_point = polygon[0]
        self.assertAlmostEqual(first_point['x'], radius, places=5)
        self.assertAlmostEqual(first_point['y'], 0, places=5)
        
        # Last point should be at end angle
        last_point = polygon[-1]
        self.assertAlmostEqual(last_point['x'], 0, places=5)
        self.assertAlmostEqual(last_point['y'], radius, places=5)
    
    @patch('ezdxf.readfile')
    def test_read_dxf_basic(self, mock_readfile):
        """Test basic DXF reading functionality"""
        # Mock DXF document structure
        mock_doc = MagicMock()
        mock_msp = MagicMock()
        mock_doc.modelspace.return_value = mock_msp
        
        # Mock a simple polyline entity
        mock_entity = MagicMock()
        mock_entity.dxftype.return_value = 'LWPOLYLINE'
        mock_entity.get_points.return_value = [(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)]
        
        mock_msp.__iter__ = lambda x: iter([mock_entity])
        mock_readfile.return_value = mock_doc
        
        # Test reading
        polygons = DXFHandler.read_dxf('dummy_path.dxf')
        
        # Should return one polygon
        self.assertEqual(len(polygons), 1)
        
        # Polygon should have 4 points (closed polygon, last point removed)
        polygon = polygons[0]
        self.assertEqual(len(polygon), 4)
        
        # Check coordinates
        expected_points = [
            {'x': 0.0, 'y': 0.0},
            {'x': 10.0, 'y': 0.0},
            {'x': 10.0, 'y': 5.0},
            {'x': 0.0, 'y': 5.0}
        ]
        
        for i, point in enumerate(polygon):
            self.assertAlmostEqual(point['x'], expected_points[i]['x'])
            self.assertAlmostEqual(point['y'], expected_points[i]['y'])
    
    @patch('ezdxf.readfile')
    def test_read_dxf_multiple_entities(self, mock_readfile):
        """Test reading DXF with multiple entities"""
        mock_doc = MagicMock()
        mock_msp = MagicMock()
        mock_doc.modelspace.return_value = mock_msp
        
        # Mock multiple entities
        mock_poly = MagicMock()
        mock_poly.dxftype.return_value = 'LWPOLYLINE'
        mock_poly.get_points.return_value = [(0, 0), (5, 0), (5, 3), (0, 3), (0, 0)]
        
        mock_line = MagicMock()
        mock_line.dxftype.return_value = 'LINE'
        mock_line.dxf.start = MagicMock(x=10, y=10)
        mock_line.dxf.end = MagicMock(x=15, y=15)
        
        # Line should be ignored (only 2 points, need at least 3)
        mock_msp.__iter__ = lambda x: iter([mock_poly, mock_line])
        mock_readfile.return_value = mock_doc
        
        polygons = DXFHandler.read_dxf('dummy_path.dxf')
        
        # Should only return the polyline (line is too short)
        self.assertEqual(len(polygons), 1)
    
    @patch('ezdxf.readfile')
    def test_read_dxf_error_handling(self, mock_readfile):
        """Test DXF reading error handling"""
        mock_readfile.side_effect = Exception("File not found")
        
        with self.assertRaises(ValueError) as context:
            DXFHandler.read_dxf('nonexistent.dxf')
        
        self.assertIn("Error reading DXF file", str(context.exception))
    
    @patch('ezdxf.new')
    def test_write_dxf_basic(self, mock_new):
        """Test basic DXF writing functionality"""
        # Mock DXF document creation
        mock_doc = MagicMock()
        mock_msp = MagicMock()
        mock_layers = MagicMock()
        
        mock_doc.modelspace.return_value = mock_msp
        mock_doc.layers = mock_layers
        mock_doc.units = None
        
        mock_new.return_value = mock_doc
        
        # Test writing
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp_file:
            try:
                DXFHandler.write_dxf(tmp_file.name, self.placement_data)
                
                # Check that document was created and saved
                mock_new.assert_called_once()
                mock_doc.saveas.assert_called_once_with(tmp_file.name)
                
                # Check that layers were created
                self.assertEqual(mock_layers.new.call_count, 2)  # CONTAINER and PARTS layers
                
                # Check that polylines were added
                self.assertGreater(mock_msp.add_lwpolyline.call_count, 0)
                
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_read_multiple_dxf_files(self):
        """Test reading multiple DXF files"""
        with patch.object(DXFHandler, 'read_dxf') as mock_read:
            # Mock successful reads for some files
            mock_read.side_effect = [
                [self.sample_polygons[0]],  # First file
                Exception("Error"),          # Second file (error)
                [self.sample_polygons[1]]   # Third file
            ]
            
            file_paths = ['file1.dxf', 'file2.dxf', 'file3.dxf']
            
            with patch('builtins.print'):  # Suppress warning prints
                all_polygons = DXFHandler.read_multiple_dxf_files(file_paths)
            
            # Should return polygons from successful reads only
            self.assertEqual(len(all_polygons), 2)
            self.assertEqual(all_polygons[0], self.sample_polygons[0])
            self.assertEqual(all_polygons[1], self.sample_polygons[1])
    
    @patch('ezdxf.readfile')
    def test_get_dxf_info(self, mock_readfile):
        """Test getting DXF file information"""
        # Mock DXF document
        mock_doc = MagicMock()
        mock_doc.dxfversion = 'AC1021'  # DXF R2007
        mock_doc.units = 1  # Millimeters
        
        mock_msp = MagicMock()
        mock_doc.modelspace.return_value = mock_msp
        
        # Mock entities
        mock_entities = []
        for entity_type in ['LWPOLYLINE', 'LINE', 'CIRCLE', 'LINE']:
            mock_entity = MagicMock()
            mock_entity.dxftype.return_value = entity_type
            mock_entities.append(mock_entity)
        
        mock_msp.__iter__ = lambda x: iter(mock_entities)
        mock_readfile.return_value = mock_doc
        
        info = DXFHandler.get_dxf_info('test.dxf')
        
        # Check info structure
        self.assertIn('version', info)
        self.assertIn('units', info)
        self.assertIn('total_entities', info)
        self.assertIn('entity_types', info)
        
        # Check values
        self.assertEqual(info['version'], 'AC1021')
        self.assertEqual(info['units'], 1)
        self.assertEqual(info['total_entities'], 4)
        self.assertEqual(info['entity_types']['LINE'], 2)
        self.assertEqual(info['entity_types']['LWPOLYLINE'], 1)
        self.assertEqual(info['entity_types']['CIRCLE'], 1)
    
    @patch('ezdxf.readfile')
    def test_get_dxf_info_error(self, mock_readfile):
        """Test DXF info error handling"""
        mock_readfile.side_effect = Exception("File error")
        
        info = DXFHandler.get_dxf_info('bad_file.dxf')
        
        self.assertIn('error', info)
        self.assertEqual(info['error'], "File error")
    
    def test_extract_points_from_entity_types(self):
        """Test point extraction from different entity types"""
        # Test with LWPOLYLINE
        mock_lwpoly = MagicMock()
        mock_lwpoly.dxftype.return_value = 'LWPOLYLINE'
        mock_lwpoly.get_points.return_value = [(0, 0), (5, 0), (5, 3)]
        
        points = DXFHandler._extract_points_from_entity(mock_lwpoly)
        expected = [{'x': 0.0, 'y': 0.0}, {'x': 5.0, 'y': 0.0}, {'x': 5.0, 'y': 3.0}]
        self.assertEqual(points, expected)
        
        # Test with LINE
        mock_line = MagicMock()
        mock_line.dxftype.return_value = 'LINE'
        mock_line.dxf.start = MagicMock(x=1, y=2)
        mock_line.dxf.end = MagicMock(x=3, y=4)
        
        points = DXFHandler._extract_points_from_entity(mock_line)
        expected = [{'x': 1.0, 'y': 2.0}, {'x': 3.0, 'y': 4.0}]
        self.assertEqual(points, expected)
        
        # Test with CIRCLE
        mock_circle = MagicMock()
        mock_circle.dxftype.return_value = 'CIRCLE'
        mock_circle.dxf.center = MagicMock(x=0, y=0)
        mock_circle.dxf.radius = 5
        
        points = DXFHandler._extract_points_from_entity(mock_circle)
        self.assertEqual(len(points), 32)  # Default 32 segments
        
        # All points should be at radius 5 from origin
        for point in points:
            distance = (point['x']**2 + point['y']**2)**0.5
            self.assertAlmostEqual(distance, 5.0, places=5)


if __name__ == '__main__':
    unittest.main()