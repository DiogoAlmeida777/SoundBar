from light.light import Light
from math import cos, radians

class SpotLight(Light):
    def __init__(self,
                 color=(1, 1, 1),
                 position=(0, 0, 0),
                 direction=(0, -1, 0),  # padrão: para baixo
                 cutoff_angle=30,       # em graus
                 inner_cutoff_angle=50,
                 attenuation=(1, 0, 0.1)
                 ):
        super().__init__(Light.SPOT)  
        self._color = color
        self._attenuation = attenuation
        self._cutoff_angle = cutoff_angle
        self._inner_cutoff_angle = inner_cutoff_angle
        self._direction = direction
        self.set_position(position)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value

    @property
    def cutoff_angle(self):
        return self._cutoff_angle

    @cutoff_angle.setter
    def cutoff_angle(self, value):
        self._cutoff_angle = value
    
    @property
    def inner_cutoff_angle(self):
        return self._inner_cutoff_angle

    @inner_cutoff_angle.setter
    def inner_cutoff_angle(self, value):
        self._inner_cutoff_angle = value
    
    @property
    def cutoff(self):
        return cos(radians(self._cutoff_angle))
    
    @property
    def inner_cutoff(self):
        return cos(radians(self._inner_cutoff_angle))


