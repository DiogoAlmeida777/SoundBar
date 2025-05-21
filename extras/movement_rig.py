import math
from core_ext.object3d import Object3D
from extras.collision_manager import CollisionManager


class MovementRig(Object3D):
    """
    Add moving forwards and backwards, left and right, 
    up and down (all local translations), as well as 
    turning left and right, and looking up and down
    """
    def __init__(self, units_per_second=3, degrees_per_second=60, mouse_sensitivity=0.1):
        # Initialize base Object3D.
        # Controls movement and turn left/right.
        super().__init__()
        # Initialize attached Object3D; controls look up/down
        self._look_attachment = Object3D()
        self.children_list = [self._look_attachment]
        self._look_attachment.parent = self
        # Control rate of movement
        self._units_per_second = units_per_second
        self._degrees_per_second = degrees_per_second 
        self._mouse_sensitivity = mouse_sensitivity
        
        # Yaw and pitch tracking
        self._pitch = 0.0
        self._pitch_limit = math.radians(89.9)

        # Customizable key mappings.
        # Defaults: W, A, S, D, R, F (move), Q, E (turn), T, G (look)
        self.KEY_MOVE_FORWARDS = "w"
        self.KEY_MOVE_BACKWARDS = "s"
        self.KEY_MOVE_LEFT = "a"
        self.KEY_MOVE_RIGHT = "d"
        self.KEY_TURN_LEFT = "q"
        self.KEY_TURN_RIGHT = "e"
        self.KEY_LOOK_UP = "t"
        self.KEY_LOOK_DOWN = "g"

        # Initialize collision manager
        self._collision_manager = CollisionManager()
        
        # Add collision objects
        self._setup_collision_objects()

    def _setup_collision_objects(self):
        """Setup collision objects for the bar"""
        # Add tables
        table_positions = [[-5, 0, -5], [-5, 0, 5], [5, 0, -5], [5, 0, 5]]
        for pos in table_positions:
            self._collision_manager.add_collision_object(pos, [2, 0, 2])  # Table size
            
        # Add bar stand
        self._collision_manager.add_collision_object([-10, 0, 12], [4, 0, 2])
        
        # Add stage
        self._collision_manager.add_collision_object([0, 0, -11.5], [8, 0, 4])
        
        # Add jukebox
        self._collision_manager.add_collision_object([0, 0, 14.5], [2, 0, 2])
        
        # Add shelf
        self._collision_manager.add_collision_object([-11.1, 0, 14.3], [2, 0, 1])
        
        # Add barstools
        for i in range(4):
            self._collision_manager.add_collision_object([-12.5 + i, 0, 11], [0.5, 0, 0.5])
            
        # Add TV and table
        self._collision_manager.add_collision_object([14, 0, -14], [2, 0, 2])
        
        # Add dance floor
        self._collision_manager.add_collision_object([0, 0, 0], [8, 0, 8])
        
        # Add mirrorball
        self._collision_manager.add_collision_object([0, 0, 0], [1, 0, 1])
        
        # Add neon sign
        self._collision_manager.add_collision_object([-14.9, 0, 5], [2, 0, 0.5])
        
        # Add exit sign
        self._collision_manager.add_collision_object([12.1, 0, 15], [1, 0, 0.5])

    # Adding and removing objects applies to look attachment.
    # Override functions from the Object3D class.
    def add(self, child):
        self._look_attachment.add(child)

    def remove(self, child):
        self._look_attachment.remove(child)

    def update(self, input_object, delta_time):
        move_amount = self._units_per_second * delta_time
        rotate_amount = self._degrees_per_second * (math.pi / 180) * delta_time
        
        # Calculate new position based on input
        new_position = list(self.local_position)
        
        # Get the current rotation matrix for camera-based movement
        rotation_matrix = self.rotation_matrix
        
        # Calculate movement direction based on camera orientation
        if input_object.is_key_pressed(self.KEY_MOVE_FORWARDS):
            # Move forward in camera direction
            forward = rotation_matrix @ [0, 0, -1]
            new_position[0] += forward[0] * move_amount
            new_position[2] += forward[2] * move_amount
        if input_object.is_key_pressed(self.KEY_MOVE_BACKWARDS):
            # Move backward in camera direction
            forward = rotation_matrix @ [0, 0, -1]
            new_position[0] -= forward[0] * move_amount
            new_position[2] -= forward[2] * move_amount
        if input_object.is_key_pressed(self.KEY_MOVE_LEFT):
            # Move left relative to camera direction
            right = rotation_matrix @ [1, 0, 0]
            new_position[0] -= right[0] * move_amount
            new_position[2] -= right[2] * move_amount
        if input_object.is_key_pressed(self.KEY_MOVE_RIGHT):
            # Move right relative to camera direction
            right = rotation_matrix @ [1, 0, 0]
            new_position[0] += right[0] * move_amount
            new_position[2] += right[2] * move_amount
            
        # Get valid position from collision manager
        valid_position = self._collision_manager.get_valid_position(
            self.local_position, new_position)
            
        # Update position
        self.set_position(valid_position)
        
        # Handle mouse-based look
        mouse_dx, mouse_dy = input_object.mouse_delta  # Get mouse delta (x, y)

        # Update yaw and pitch based on mouse movement
        delta_yaw = -math.radians(mouse_dx * self._mouse_sensitivity)
        delta_pitch = -math.radians(mouse_dy * self._mouse_sensitivity)

        self.rotate_y(delta_yaw)
        # Apply pitch with clamping
        new_pitch = self._pitch + delta_pitch
        new_pitch = max(-self._pitch_limit, min(self._pitch_limit, new_pitch))
        pitch_change = new_pitch - self._pitch
        self._pitch = new_pitch
        self._look_attachment.rotate_x(pitch_change)
