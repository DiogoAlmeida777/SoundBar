from light.directional import DirectionalLight
import math

class DirectionalSpotLight(DirectionalLight):
    def __init__(self, 
                 color=(1, 1, 1), 
                 direction=(0, -1, 0),
                 cone_angle=30,  # ângulo do cone em graus
                 distance=10):   # distância do cone
        super().__init__(color, direction)
        self._cone_angle = cone_angle
        self._distance = distance
        self._update_camera_bounds()

    def _update_camera_bounds(self):
        # Calcula os limites da câmera baseado no ângulo do cone
        # Converte o ângulo para radianos
        angle_rad = math.radians(self._cone_angle)
        # Calcula o tamanho do cone na distância especificada
        size = self._distance * math.tan(angle_rad)
        # Define os limites da câmera para criar um cone
        self._camera_bounds = (-size, size, -size, size, 0, self._distance)

    @property
    def camera_bounds(self):
        return self._camera_bounds

    @property
    def cone_angle(self):
        return self._cone_angle

    @cone_angle.setter
    def cone_angle(self, value):
        self._cone_angle = value
        self._update_camera_bounds()

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, value):
        self._distance = value
        self._update_camera_bounds() 