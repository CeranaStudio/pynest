#!/usr/bin/env python3
"""
PyNest - DXF Nesting Tool

A Python implementation of nesting algorithms based on deepnest and no_fit_polygon.
Reads DXF files, performs nesting optimization, and outputs results.
"""

import argparse
import os
import sys
import time
from pathlib import Path

from nester import Nester
from nester.dxf_handler import DXFHandler


def print_progress(stats):
    """Print progress information"""
    print(f"Generation {stats['generation']}: "
          f"Best fitness: {stats['best_fitness']:.2f}, "
          f"Placed: {stats['best_placed']}/{stats['total_parts']}, "
          f"Avg fitness: {stats['avg_fitness']:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="PyNest - DXF Nesting Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --container container.dxf --parts part1.dxf part2.dxf --output result.dxf
  python main.py -c bin.dxf -p *.dxf -o nested.dxf --spacing 2 --rotations 8
  python main.py --container container.dxf --parts-dir ./parts/ --output result.dxf
        """
    )
    
    # Input arguments
    parser.add_argument('-c', '--container', required=True,
                       help='DXF file containing the container/bin shape')
    
    parser.add_argument('-p', '--parts', nargs='*',
                       help='DXF files containing parts to nest')
    
    parser.add_argument('--parts-dir',
                       help='Directory containing DXF part files')
    
    # Output arguments
    parser.add_argument('-o', '--output', required=True,
                       help='Output DXF file path')
    
    # Algorithm parameters
    parser.add_argument('--spacing', type=float, default=0,
                       help='Spacing between parts for laser kerf, CNC offset etc. (default: 0)')
    
    parser.add_argument('--curve-tolerance', type=float, default=0.3,
                       help='Maximum error for curve approximation (default: 0.3)')
    
    parser.add_argument('--rotations', type=int, default=4,
                       help='Number of rotation angles to try (default: 4)')
    
    parser.add_argument('--population-size', type=int, default=10,
                       help='Genetic algorithm population size (default: 10)')
    
    parser.add_argument('--mutation-rate', type=int, default=10,
                       help='Mutation rate percentage 1-50 (default: 10)')
    
    parser.add_argument('--max-generations', type=int, default=100,
                       help='Maximum number of generations (default: 100)')
    
    parser.add_argument('--explore-concave', action='store_true',
                       help='Explore concave areas for better placement (slower but better results)')
    
    parser.add_argument('--use-holes', action='store_true',
                       help='Enable part-in-part placement (experimental)')
    
    # Other options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--info', action='store_true',
                       help='Show information about input files and exit')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.container):
        print(f"Error: Container file '{args.container}' not found")
        sys.exit(1)
    
    # Collect part files
    part_files = []
    
    if args.parts:
        for part_file in args.parts:
            if os.path.exists(part_file):
                part_files.append(part_file)
            else:
                print(f"Warning: Part file '{part_file}' not found")
    
    if args.parts_dir:
        if os.path.isdir(args.parts_dir):
            for file in Path(args.parts_dir).glob('*.dxf'):
                part_files.append(str(file))
        else:
            print(f"Warning: Parts directory '{args.parts_dir}' not found")
    
    if not part_files:
        print("Error: No part files found")
        sys.exit(1)
    
    if args.info:
        # Show file information and exit
        print(f"Container file: {args.container}")
        container_info = DXFHandler.get_dxf_info(args.container)
        if 'error' in container_info:
            print(f"  Error: {container_info['error']}")
        else:
            print(f"  Version: {container_info['version']}")
            print(f"  Entities: {container_info['total_entities']}")
            print(f"  Types: {container_info['entity_types']}")
        
        print(f"\nPart files ({len(part_files)}):")
        for part_file in part_files:
            print(f"  {part_file}")
            part_info = DXFHandler.get_dxf_info(part_file)
            if 'error' in part_info:
                print(f"    Error: {part_info['error']}")
            else:
                print(f"    Entities: {part_info['total_entities']}")
        sys.exit(0)
    
    try:
        print("PyNest - DXF Nesting Tool")
        print("=" * 40)
        
        # Read container
        print(f"Reading container from: {args.container}")
        container_polygons = DXFHandler.read_dxf(args.container)
        
        if not container_polygons:
            print("Error: No valid polygons found in container file")
            sys.exit(1)
        
        # Use the first (largest) polygon as container
        container_polygon = max(container_polygons, key=lambda p: abs(sum((p[i]['x'] * p[(i+1) % len(p)]['y'] - p[(i+1) % len(p)]['x'] * p[i]['y']) for i in range(len(p)))))
        print(f"Container polygon with {len(container_polygon)} points")
        
        # Read parts
        print(f"Reading {len(part_files)} part files...")
        all_part_polygons = DXFHandler.read_multiple_dxf_files(part_files)
        
        if not all_part_polygons:
            print("Error: No valid polygons found in part files")
            sys.exit(1)
        
        print(f"Found {len(all_part_polygons)} part polygons")
        
        # Configure nester
        config = {
            'curve_tolerance': args.curve_tolerance,
            'spacing': args.spacing,
            'rotations': args.rotations,
            'population_size': args.population_size,
            'mutation_rate': args.mutation_rate,
            'max_generations': args.max_generations,
            'explore_concave': args.explore_concave,
            'use_holes': args.use_holes
        }
        
        print(f"Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Initialize nester
        nester = Nester(config)
        nester.add_container(container_polygon)
        nester.add_parts(all_part_polygons)
        
        # Run nesting
        print(f"\nStarting nesting optimization...")
        start_time = time.time()
        
        progress_callback = print_progress if args.verbose else None
        result = nester.run(progress_callback=progress_callback)
        
        end_time = time.time()
        
        # Print results
        print(f"\nNesting completed in {end_time - start_time:.2f} seconds")
        print(f"Results:")
        print(f"  Placed parts: {result['placed_count']}/{result['total_parts']}")
        print(f"  Utilization: {result['utilization']*100:.1f}%")
        print(f"  Final fitness: {result['fitness']:.2f}")
        
        if result['placed_count'] < result['total_parts']:
            print(f"  Warning: {result['total_parts'] - result['placed_count']} parts could not be placed")
        
        # Save result
        print(f"\nSaving result to: {args.output}")
        placement_data = nester.get_placement_data()
        
        if placement_data:
            DXFHandler.write_dxf(args.output, placement_data)
            print("Result saved successfully!")
        else:
            print("Error: No placement data to save")
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()