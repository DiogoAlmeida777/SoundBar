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
        self._last_mouse_pos = pygame.mouse.get_pos()

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

        self._mouse_delta = pygame.mouse.get_rel()
        # Iterate to detect changes since last check
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

    @property
    def mouse_delta(self):
        return self._mouse_delta