from geometry.ellipsoid import EllipsoidGeometry


class SphereGeometry(EllipsoidGeometry):
    def __init__(self, radius=1, theta_segments=32, phi_segments=16):
        super().__init__(2*radius, 2*radius, 2*radius, theta_segments, phi_segments)