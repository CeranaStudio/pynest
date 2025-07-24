#!/usr/bin/env python3
"""
PyNest Example Usage

This script demonstrates how to use PyNest programmatically without DXF files.
"""

import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from nester import Nester


def create_rectangle(width, height, x=0, y=0):
    """Create a rectangle polygon"""
    return [
        {'x': x, 'y': y},
        {'x': x + width, 'y': y},
        {'x': x + width, 'y': y + height},
        {'x': x, 'y': y + height}
    ]


def create_circle(radius, center_x=0, center_y=0, segments=16):
    """Create a circle polygon"""
    points = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append({'x': x, 'y': y})
    return points


def create_triangle(base, height, x=0, y=0):
    """Create a triangle polygon"""
    return [
        {'x': x, 'y': y},
        {'x': x + base, 'y': y},
        {'x': x + base/2, 'y': y + height}
    ]


def create_l_shape(width, height, thickness):
    """Create an L-shaped polygon"""
    return [
        {'x': 0, 'y': 0},
        {'x': width, 'y': 0},
        {'x': width, 'y': thickness},
        {'x': thickness, 'y': thickness},
        {'x': thickness, 'y': height},
        {'x': 0, 'y': height}
    ]


def visualize_result(placement_data):
    """Visualize the nesting result using matplotlib"""
    if not placement_data:
        print("No placement data to visualize")
        return
    
    num_bins = len(placement_data)
    fig, axes = plt.subplots(1, num_bins, figsize=(6 * num_bins, 6))
    
    if num_bins == 1:
        axes = [axes]
    
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    for bin_index, bin_data in enumerate(placement_data):
        ax = axes[bin_index] if num_bins > 1 else axes[0]
        
        # Draw container
        container_points = bin_data['container']['points']
        container_coords = [(p['x'], p['y']) for p in container_points]
        container_patch = patches.Polygon(container_coords, fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(container_patch)
        
        # Draw parts
        for i, part in enumerate(bin_data['parts']):
            part_coords = [(p['x'], p['y']) for p in part['placed_points']]
            color = colors[i % len(colors)]
            part_patch = patches.Polygon(part_coords, fill=True, facecolor=color, 
                                       alpha=0.7, edgecolor='black', linewidth=1)
            ax.add_patch(part_patch)
            
            # Add part ID label
            centroid_x = sum(p['x'] for p in part['placed_points']) / len(part['placed_points'])
            centroid_y = sum(p['y'] for p in part['placed_points']) / len(part['placed_points'])
            ax.text(centroid_x, centroid_y, str(part['id']), 
                   ha='center', va='center', fontweight='bold')
        
        # Set equal aspect ratio and limits
        ax.set_aspect('equal')
        
        # Calculate bounds for nice view
        all_points = container_points + [p for part in bin_data['parts'] for p in part['placed_points']]
        if all_points:
            min_x = min(p['x'] for p in all_points) - 10
            max_x = max(p['x'] for p in all_points) + 10
            min_y = min(p['y'] for p in all_points) - 10
            max_y = max(p['y'] for p in all_points) + 10
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
        
        ax.set_title(f'Bin {bin_index + 1}')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def example_basic():
    """Basic nesting example with simple shapes"""
    print("Running basic nesting example...")
    
    # Create container (a 200x200 square)
    container = create_rectangle(200, 200)
    
    # Create parts to nest
    parts = [
        create_rectangle(60, 40),     # Rectangle
        create_rectangle(50, 30),     # Smaller rectangle  
        create_circle(25, segments=12), # Circle
        create_triangle(40, 50),      # Triangle
        create_rectangle(30, 70),     # Tall rectangle
    ]
    
    # Configure nester
    config = {
        'spacing': 2,          # 2 units spacing between parts
        'rotations': 4,        # Try 0°, 90°, 180°, 270°
        'population_size': 15,
        'mutation_rate': 15,
        'max_generations': 50
    }
    
    # Run nesting
    nester = Nester(config)
    nester.add_container(container)
    nester.add_parts(parts)
    
    def progress_callback(stats):
        if stats['generation'] % 10 == 0:
            print(f"Generation {stats['generation']}: "
                  f"Placed {stats['best_placed']}/{stats['total_parts']} parts, "
                  f"Fitness: {stats['best_fitness']:.2f}")
    
    result = nester.run(progress_callback=progress_callback)
    
    # Print results
    print(f"\nResults:")
    print(f"  Placed: {result['placed_count']}/{result['total_parts']} parts")
    print(f"  Utilization: {result['utilization']*100:.1f}%")
    print(f"  Fitness: {result['fitness']:.2f}")
    
    # Visualize
    placement_data = nester.get_placement_data()
    visualize_result(placement_data)
    
    return result


def example_complex():
    """Complex nesting example with irregular shapes"""
    print("Running complex nesting example...")
    
    # Create a more complex container
    container = [
        {'x': 0, 'y': 0},
        {'x': 300, 'y': 0},
        {'x': 300, 'y': 200},
        {'x': 250, 'y': 200},
        {'x': 250, 'y': 100},
        {'x': 150, 'y': 100},
        {'x': 150, 'y': 250},
        {'x': 0, 'y': 250}
    ]
    
    # Create various parts
    parts = [
        create_l_shape(80, 80, 20),      # L-shape
        create_rectangle(60, 40),         # Rectangle
        create_circle(30, segments=16),   # Circle
        create_triangle(50, 60),          # Triangle
        create_rectangle(40, 80),         # Tall rectangle
        create_rectangle(70, 30),         # Wide rectangle
        create_circle(20, segments=12),   # Small circle
        create_triangle(35, 40),          # Small triangle
    ]
    
    # Configure with more aggressive settings
    config = {
        'curve_tolerance': 0.1,   # More precise curve approximation
        'spacing': 3,
        'rotations': 8,           # Try 8 different angles
        'population_size': 20,
        'mutation_rate': 20,
        'max_generations': 100,
        'explore_concave': True,  # Enable concave area exploration
        'use_holes': False        # Disable part-in-part for now
    }
    
    # Run nesting
    nester = Nester(config)
    nester.add_container(container)
    nester.add_parts(parts)
    
    def progress_callback(stats):
        if stats['generation'] % 20 == 0:
            print(f"Generation {stats['generation']}: "
                  f"Placed {stats['best_placed']}/{stats['total_parts']} parts, "
                  f"Fitness: {stats['best_fitness']:.2f}")
    
    result = nester.run(progress_callback=progress_callback)
    
    # Print results
    print(f"\nResults:")
    print(f"  Placed: {result['placed_count']}/{result['total_parts']} parts")
    print(f"  Utilization: {result['utilization']*100:.1f}%")
    print(f"  Fitness: {result['fitness']:.2f}")
    
    # Visualize
    placement_data = nester.get_placement_data()
    visualize_result(placement_data)
    
    return result


def main():
    """Run examples"""
    print("PyNest Examples")
    print("=" * 40)
    
    # Run basic example
    print("\n1. Basic Example:")
    example_basic()
    
    # Run complex example
    print("\n2. Complex Example:")
    example_complex()
    
    print("\nExamples completed!")


if __name__ == "__main__":
    main()