"""Input management"""
import pygame


class Input(object):
    """Manages the users commands"""
    def __init__(self) -> None:
        """User terminated?"""
        self.quit = False
        # lists to store key states
        # down, up: discrete event; lasts for one iteration
        # pressed: continuous event, between down and up events
        self.key_down_list = []
        self.key_pressed_list = []
        self.key_up_list = []

         # Mouse movement
        self._mouse_delta = (0, 0)
        
        # Mouse wrapping settings
        self._wrap_mouse = True
        self._screen_size = pygame.display.get_surface().get_size()
        self._center_x = self._screen_size[0] // 2
        self._center_y = self._screen_size[1] // 2
        self._mouse_was_repositioned = False  # Track when we reposition mouse

        # Lock and hide mouse for FPS-style control (optional)
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
    
    # functions to check key states
    def is_key_down(self, keyCode):
        """Check is key is pressed"""
        return keyCode in self.key_down_list
    def is_key_pressed(self, keyCode):
        """Check if key os pressed"""
        return keyCode in self.key_pressed_list
    def is_key_up(self, keyCode):
        """Check if key was released"""
        return keyCode in self.key_up_list

    def update(self):
        """Manage user input events"""
        # Reset discrete key states
        self.key_down_list = []
        self.key_up_list = []

        # FIRST: Capture mouse movement before any repositioning
        raw_mouse_delta = pygame.mouse.get_rel()
        
        # If mouse was repositioned last frame, ignore this delta to prevent teleports
        if self._mouse_was_repositioned:
            self._mouse_delta = (0, 0)
            self._mouse_was_repositioned = False
        else:
            self._mouse_delta = raw_mouse_delta
        
        # THEN: Handle mouse centering for continuous camera rotation
        if self._wrap_mouse:
            mouse_pos = pygame.mouse.get_pos()
            x, y = mouse_pos
            
            # Check if mouse is at screen edges (use actual edges, not margin)
            edge_margin = 5  # Very small margin, only trigger at actual edges
            
            should_recenter = (x <= edge_margin or x >= self._screen_size[0] - edge_margin or 
                             y <= edge_margin or y >= self._screen_size[1] - edge_margin)
            
            if should_recenter:
                # Move mouse to center of screen
                pygame.mouse.set_pos(self._center_x, self._center_y)
                # Set flag to ignore next frame's delta
                self._mouse_was_repositioned = True
                # Clear the rel movement buffer
                pygame.mouse.get_rel()
        
        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
            # Check for key-down and key-up events;
            # get name of key from event and append to or remove from corresponding lists
            if event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                self.key_down_list.append(key_name)
                self.key_pressed_list.append(key_name)
                if key_name == "escape":
                    self.quit = True
            if event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key)
                self.key_pressed_list.remove(key_name)
                self.key_up_list.append(key_name)

    def update_screen_size(self):
        """Update screen size for mouse wrapping (call when changing fullscreen mode)"""
        self._screen_size = pygame.display.get_surface().get_size()
        self._center_x = self._screen_size[0] // 2
        self._center_y = self._screen_size[1] // 2
        self._mouse_was_repositioned = False  # Reset flag when screen size changes

    @property
    def mouse_delta(self):
        return self._mouse_delta