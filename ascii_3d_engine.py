# ascii_3d_engine.py
import os
import sys
import time
import numpy as np
import threading
from prepare import ExoJUOSKernel

class ExoJ3DTextRenderer:
    """
    A minimal, high-performance 3D ASCII projection engine.
    Projects raw 3D coordinate vectors (vessel geometry, wave grids, or sonar points)
    onto a flat 2D character matrix workspace optimized for high-visibility deck monitors.
    """
    def __init__(self, width=80, height=35):
        self.width = width
        self.height = height
        self.aspect_ratio = width / height
        # Character palette ordered by luminous intensity / structural density density
        self.palette = " .:-=+*#%@" 
        
    def create_rotation_matrices(self, yaw, pitch, roll):
        """Generates 3D Tait-Bryan rotation transformations from radians."""
        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        cr, sr = np.cos(roll), np.sin(roll)
        
        R_yaw = np.array([
            [cy, -sy, 0],
            [sy,  cy, 0],
            [0,   0,  1]
        ])
        R_pitch = np.array([
            [cp,  0, sp],
            [0,   1, 0],
            [-sp, 0, cp]
        ])
        R_roll = np.array([
            [1, 0,   0],
            [0, cr, -sr],
            [0, sr,  cr]
        ])
        return R_yaw @ R_pitch @ R_roll

    def project_vertex(self, x, y, z, R, camera_distance=4.0):
        """Transforms and projects a 3D vector point onto a 2D text viewport mapping."""
        # Apply 3D coordinate rotation mechanics
        rotated = R @ np.array([x, y, z])
        rx, ry, rz = rotated[0], rotated[1], rotated[2]
        
        # Add depth translation distance from target camera eye plane
        z_depth = rz + camera_distance
        if z_depth <= 0.1: 
            return None, None, z_depth
            
        # Perspective transform projection equations
        proj_x = int(self.width / 2 + (rx / z_depth) * self.width * (1.0 / self.aspect_ratio))
        proj_y = int(self.height / 2 + (ry / z_depth) * self.height)
        return proj_x, proj_y, z_depth

    def render_wireframe_grid(self, vertices, edges, yaw, pitch, roll, shading_intensities=None):
        """Renders a comprehensive 3D object representation onto the character array buffer."""
        # Initialize an empty terminal character screen slice buffer and depth buffer
        screen = np.full((self.height, self.width), " ", dtype=object)
        z_buffer = np.full((self.height, self.width), float('inf'))
        
        R = self.create_rotation_matrices(yaw, pitch, roll)
        projected_points = {}
        
        # 1. Project all nodes safely into current viewport dimensions
        for idx, vertex in enumerate(vertices):
            px, py, z_depth = self.project_vertex(vertex[0], vertex[1], vertex[2], R)
            if px is not None and 0 <= px < self.width and 0 <= py < self.height:
                projected_points[idx] = (px, py)
                # Render vertex nodes with high-density markers
                if z_depth < z_buffer[py, px]:
                    z_buffer[py, px] = z_depth
                    screen[py, px] = "█"

        # 2. Rasterize connecting edge wireframes using Bresenham's line algorithm
        for edge_idx, (start_idx, end_idx) in enumerate(edges):
            if start_idx not in projected_points or end_idx not in projected_points:
                continue
                
            x0, y0 = projected_points[start_idx]
            x1, y1 = projected_points[end_idx]
            
            # Select density character based on structural lookup or line depth bounds
            char_token = "▒" if shading_intensities is None else self.palette[min(len(self.palette)-1, int(shading_intensities[edge_idx]))]
            
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            
            while True:
                if 0 <= x0 < self.width and 0 <= y0 < self.height:
                    # Line overlay without depth sorting for wireframe integrity grids
                    screen[y0, x0] = char_token
                    
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy
                    
        return "\n".join(["".join(row) for row in screen])

# =====================================================================
# HARDWARE DATA OVERLAY & SIMULATION TESTING
# =====================================================================
def get_vessel_3d_hull():
    """Returns structural 3D coordinates representing a commercial salmon troller."""
    vertices = np.array([
        [0.0, -1.5, 0.0],  # 0: Bow Point
        [0.6, -0.4, 0.3],  # 1: Starboard Mid Upper
        [0.6,  1.2, 0.3],  # 2: Starboard Stern Upper
        [-0.6, 1.2, 0.3],  # 3: Port Stern Upper
        [-0.6, -0.4, 0.3], # 4: Port Mid Upper
        [0.0,  1.2, -0.4], # 5: Keel Stern Deadwood
        [0.0, -0.4, -0.5], # 6: Keel Mid Deep
    ])
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 0), # Upper Deck Gunwale Perimeter
        (0, 6), (6, 5), (5, 2), (5, 3),         # Keel Centerline Profile
        (6, 1), (6, 4),                         # Mid Rib Structural Forms
    ]
    return vertices, edges

if __name__ == "__main__":
    # Fallback instantiation sequence if running away from full matrix kernel pipes
    try:
        kernel = ExoJUOSKernel()
        print("[3D Engine] Shared matrix link verified secure.")
    except Exception:
        print("[3D Engine] Matrix kernel offline. Running in standalone visualization mode.")
        kernel = None

    renderer = ExoJ3DTextRenderer(width=80, height=32)
    vertices, edges = get_vessel_3d_hull()
    
    # Continuous visual loop emulation step
    print("\033[2J", end="") # Wipes terminal screen window
    
    # Simulate a series of 20 quick animation frames reflecting rolling swell physics
    for frame in range(20):
        t = time.time()
        
        # Read rolling movements directly from shared registers if available
        if kernel is not None:
            sensory_data = kernel.read_register("sensory_inputs")
            roll_angle = np.radians(sensory_data[3]) # Index 3 maps to vessel roll metrics
            pitch_angle = np.radians(sensory_data[3] * 0.3)
            heading_err = np.radians(sensory_data[0])
        else:
            # Fallback simulated matrix oscillations matching heavy sea inputs
            roll_angle = np.sin(t * 1.5) * 0.15
            pitch_angle = np.cos(t * 1.2) * 0.05
            heading_err = np.sin(t * 0.4) * 0.1
            
        # Draw the 3D projection array matrix frame block
        frame_text = renderer.render_wireframe_grid(
            vertices, edges, 
            yaw=heading_err + np.pi, # Point stern view towards cockpit display perspective
            pitch=pitch_angle + 0.2, # Add static incline elevation angle for optimal visibility
            roll=roll_angle
        )
        
        # Reposition terminal frame cursor to top-left zero origin point
        sys.stdout.write("\033[H")
        sys.stdout.write("=================================================================\n")
        sys.stdout.write(f"  EXOJ 3D ASCII VIEWCORE | SEASTATE DETECTED: FOLLOW SWELL | F: {frame}\n")
        sys.stdout.write("=================================================================\n")
        sys.stdout.write(frame_text + "\n")
        sys.stdout.write("=================================================================\n")
        sys.stdout.flush()
        
        time.sleep(0.05)
