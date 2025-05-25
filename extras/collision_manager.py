import numpy as np
from core_ext.object3d import Object3D
from core_ext.mesh import Mesh
from geometry.box import BoxGeometry
from material.transparent import TransparentMaterial

class CollisionManager:
    def __init__(self, scene=None):
        # Define boundaries of the bar
        self.boundaries = {
            'x_min': -15,  # Left wall
            'x_max': 15,   # Right wall
            'z_min': -15,  # Back wall
            'z_max': 15    # Front wall
        }
        
        # Define collision objects (tables, bar, etc.)
        self.collision_objects = []
        
        # Store scene reference for adding debug boxes
        self.scene = scene
        self.debug_boxes = []
        
    def add_collision_object(self, position, size, height=3.0, name=""):
        """Add a collision object with its position, size, height and optional name"""
        self.collision_objects.append({
            'position': position,
            'size': size,
            'height': height,
            'name': name
        })
        
        # Create debug visualization box if scene is provided
        if self.scene is not None:
            self.create_debug_box(position, size, height, name)
        
    def create_debug_box(self, position, size, height, name=""):
        """Create a red debug box to visualize collision area"""
        # Create box geometry with the collision size and custom height
        box_geo = BoxGeometry(width=size[0], height=height, depth=size[2])
        
        # Create red transparent material
        box_material = TransparentMaterial(
            color=[1.0, 0.0, 0.0],  # Red color
            opacity=0.3  # Semi-transparent
        )
        
        # Create mesh
        debug_box = Mesh(box_geo, box_material)
        debug_box.set_position([position[0], height/2, position[2]])  # Center at half height
        
        # Add to scene and store reference with name
        self.scene.add(debug_box)
        self.debug_boxes.append({
            'mesh': debug_box,
            'name': name,
            'position': position,
            'size': size,
            'height': height
        })
        
    def remove_debug_boxes(self):
        """Remove all debug boxes from the scene"""
        if self.scene is not None:
            for box in self.debug_boxes:
                self.scene.remove(box['mesh'])
        self.debug_boxes.clear()
        
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