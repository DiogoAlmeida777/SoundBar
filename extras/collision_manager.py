import numpy as np
from core_ext.object3d import Object3D

class CollisionManager:
    def __init__(self):
        # Define boundaries of the bar
        self.boundaries = {
            'x_min': -15,  # Left wall
            'x_max': 15,   # Right wall
            'z_min': -15,  # Back wall
            'z_max': 15    # Front wall
        }
        
        # Define collision objects (tables, bar, etc.)
        self.collision_objects = []
        
    def add_collision_object(self, position, size):
        """Add a collision object with its position and size"""
        self.collision_objects.append({
            'position': position,
            'size': size
        })
        
    def check_collision(self, position, radius=0.5):
        """Check if a position collides with any boundaries or objects"""
        # Check boundaries
        if (position[0] - radius < self.boundaries['x_min'] or 
            position[0] + radius > self.boundaries['x_max'] or
            position[2] - radius < self.boundaries['z_min'] or
            position[2] + radius > self.boundaries['z_max']):
            return True
            
        # Check collision objects
        for obj in self.collision_objects:
            obj_pos = obj['position']
            obj_size = obj['size']
            
            # Simple box collision
            if (abs(position[0] - obj_pos[0]) < (radius + obj_size[0]/2) and
                abs(position[2] - obj_pos[2]) < (radius + obj_size[2]/2)):
                return True
                
        return False
        
    def get_valid_position(self, current_pos, new_pos, radius=0.5):
        """Get a valid position that doesn't collide with anything"""
        if not self.check_collision(new_pos, radius):
            return new_pos
            
        # If collision occurs, try to move only in x or z direction
        test_pos_x = [new_pos[0], current_pos[1], current_pos[2]]
        if not self.check_collision(test_pos_x, radius):
            return test_pos_x
            
        test_pos_z = [current_pos[0], current_pos[1], new_pos[2]]
        if not self.check_collision(test_pos_z, radius):
            return test_pos_z
            
        # If both x and z movements cause collisions, stay in current position
        return current_pos 