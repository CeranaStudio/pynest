# PyNest - Python Nesting Algorithm

PyNest is a Python implementation of 2D nesting algorithms based on the deepnest and no_fit_polygon projects. It provides efficient polygon nesting using genetic algorithms and No Fit Polygon (NFP) calculations.

## Features

- **DXF File Support**: Read and write DXF files for CAD integration
- **Genetic Algorithm Optimization**: Uses genetic algorithms to find optimal part arrangements
- **No Fit Polygon (NFP)**: Efficient collision detection using NFP calculations
- **Configurable Parameters**: Spacing, rotations, population size, and more
- **Command Line Interface**: Easy-to-use CLI for batch processing
- **Python API**: Programmatic access for integration into other applications

## Installation

1. Clone the repository with submodules:
```bash
git clone --recursive https://github.com/CeranaStudio/pynest.git
cd pynest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The reference implementations (Deepnest and no_fit_polygon) should be added as git submodules:

```bash
# After cloning, add reference repositories as submodules
git submodule add https://github.com/Jack000/Deepnest.git ref/Deepnest
git submodule add https://github.com/danielgindi/no_fit_polygon.git ref/no_fit_polygon
```

## Quick Start

### Command Line Usage

```bash
# Basic usage
python main.py --container container.dxf --parts part1.dxf part2.dxf --output result.dxf

# With custom parameters
python main.py -c bin.dxf -p *.dxf -o nested.dxf --spacing 2 --rotations 8 --max-generations 200 --explore-concave

# Process all DXF files in a directory
python main.py --container container.dxf --parts-dir ./parts/ --output result.dxf
```

### Python API Usage

```python
from nester import Nester

# Create container and parts (list of points)
container = [
    {'x': 0, 'y': 0},
    {'x': 200, 'y': 0},
    {'x': 200, 'y': 200},
    {'x': 0, 'y': 200}
]

parts = [
    [{'x': 0, 'y': 0}, {'x': 60, 'y': 0}, {'x': 60, 'y': 40}, {'x': 0, 'y': 40}],
    [{'x': 0, 'y': 0}, {'x': 50, 'y': 0}, {'x': 50, 'y': 30}, {'x': 0, 'y': 30}]
]

# Configure and run nesting
config = {
    'spacing': 2,
    'rotations': 4,
    'population_size': 15,
    'max_generations': 100
}

nester = Nester(config)
nester.add_container(container)
nester.add_parts(parts)

result = nester.run()
print(f"Placed {result['placed_count']}/{result['total_parts']} parts")
print(f"Utilization: {result['utilization']*100:.1f}%")
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `curve_tolerance` | 0.3 | Maximum error for curve approximation (lower = more precise) |
| `spacing` | 0 | Minimum spacing between parts (laser kerf, CNC offset, etc.) |
| `rotations` | 4 | Number of rotation angles to try (360°/n) |
| `population_size` | 10 | Genetic algorithm population size |
| `mutation_rate` | 10 | Mutation rate percentage (1-50) |
| `max_generations` | 100 | Maximum number of generations |
| `explore_concave` | False | Explore concave areas for better placement (slower but better) |
| `use_holes` | False | Enable part-in-part placement (experimental) |

## Command Line Options

```
positional arguments:
  -c, --container      DXF file containing the container/bin shape
  -p, --parts          DXF files containing parts to nest
  --parts-dir          Directory containing DXF part files
  -o, --output         Output DXF file path

algorithm parameters:
  --curve-tolerance    Maximum error for curve approximation (default: 0.3)
  --spacing            Spacing between parts for laser kerf etc. (default: 0)
  --rotations          Number of rotation angles (default: 4)
  --population-size    GA population size (default: 10)
  --mutation-rate      Mutation rate percentage 1-50 (default: 10)
  --max-generations    Maximum generations (default: 100)
  --explore-concave    Explore concave areas for better placement
  --use-holes          Enable part-in-part placement (experimental)

other options:
  --verbose, -v        Verbose output
  --info               Show file information and exit
```

## Examples

### Run Examples

```bash
# Run interactive examples with visualization
python example.py

# Run all tests
python run_tests.py

# Run specific test
python run_tests.py tests/test_nester.py
```

This will run two examples:
1. **Basic Example**: Simple shapes (rectangles, circles, triangles)
2. **Complex Example**: Irregular shapes and complex container

### File Information

```bash
# Get information about DXF files
python main.py --container container.dxf --parts *.dxf --info
```

## Algorithm Details

PyNest implements a genetic algorithm with the following components:

1. **Genetic Algorithm**: Optimizes the order and rotation of parts
2. **No Fit Polygon (NFP)**: Calculates valid placement positions
3. **Placement Worker**: Finds optimal positions using NFP data
4. **Fitness Evaluation**: Maximizes utilization and minimizes waste

### Genetic Algorithm Process:
1. Initialize population with random part orders and rotations
2. Evaluate fitness of each individual using NFP calculations
3. Select parents using tournament selection
4. Create offspring through crossover and mutation
5. Repeat until convergence or maximum generations

### No Fit Polygon:
- **Inner NFP**: Valid positions for placing a part inside a container
- **Outer NFP**: Positions where parts don't overlap
- Uses Minkowski difference for efficient calculation

## DXF Support

PyNest supports reading the following DXF entities:
- LWPOLYLINE (Lightweight Polylines)
- POLYLINE (Regular Polylines)
- LINE (Line segments)
- CIRCLE (Converted to polygons)
- ARC (Converted to polylines)
- SPLINE (Approximated as polylines)

Output DXF files contain:
- Container outline on "CONTAINER" layer (red)
- Nested parts on "PARTS" layer (yellow)

## Limitations

- Only 2D nesting (no 3D support)
- Polygons must be simple (no self-intersections)
- No support for holes in polygons (yet)
- Memory usage grows with number of parts and complexity

## Performance Tips

- Start with smaller population sizes and fewer generations for quick results
- Increase `rotations` for better optimization (but slower performance)
- Use appropriate `spacing` values to avoid overlaps
- Sort parts by area (larger first) for better results

## Dependencies

- `numpy`: Numerical computations
- `pyclipper`: Polygon clipping and offsetting
- `matplotlib`: Visualization (optional)
- `ezdxf`: DXF file reading/writing
- `shapely`: Geometric operations

## References

This project is inspired by and references:
- [Deepnest](https://github.com/Jack000/Deepnest) - Web-based nesting application (included as submodule)
- [no_fit_polygon](https://github.com/danielgindi/no_fit_polygon) - NFP calculation library (included as submodule)

The algorithms are reimplemented in Python based on the concepts from these projects.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Roadmap

- [ ] Support for holes in polygons
- [ ] Multi-sheet nesting
- [ ] GUI interface
- [ ] Performance optimizations
- [ ] More DXF entity support
- [ ] SVG file support