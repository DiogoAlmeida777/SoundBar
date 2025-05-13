import OpenGL.GL as GL
import pygame
import numpy as np

from core_ext.mesh import Mesh
from light.light import Light
from light.shadow import Shadow


class Renderer:
    def __init__(self, clear_color=(0, 0, 0)):
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_MULTISAMPLE)  # Antialiasing
        self.clear_color = clear_color
        GL.glClearColor(*clear_color, 1)
        self._window_size = pygame.display.get_surface().get_size()
        self._shadows_enabled = False

    @property
    def window_size(self):
        return self._window_size

    @property
    def shadow_object(self):
        return self._shadow_object

    def render(self, scene, camera, clear_color=True, clear_depth=True, render_target=None):
        descendant_list = scene.descendant_list
        mesh_list = list(filter(lambda x: isinstance(x, Mesh), descendant_list))

        # Shadow pass
        if self._shadows_enabled:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._shadow_object.render_target.framebuffer_ref)
            GL.glViewport(0, 0, self._shadow_object.render_target.width, self._shadow_object.render_target.height)
            GL.glClearColor(1, 1, 1, 1)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            GL.glUseProgram(self._shadow_object.material.program_ref)
            self._shadow_object.update_internal()

            for mesh in mesh_list:
                if not mesh.visible:
                    continue
                if mesh.material.setting_dict["drawStyle"] != GL.GL_TRIANGLES:
                    continue
                GL.glBindVertexArray(mesh.vao_ref)
                self._shadow_object.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
                for var_name, uniform_obj in self._shadow_object.material.uniform_dict.items():
                    uniform_obj.upload_data()
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, mesh.geometry.vertex_count)

            GL.glClearColor(*self.clear_color, 1)

        # Main render pass
        if render_target is None:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            GL.glViewport(0, 0, *self._window_size)
        else:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, render_target.framebuffer_ref)
            GL.glViewport(0, 0, render_target.width, render_target.height)

        if clear_color:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        if clear_depth:
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

        # Enable blending
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        camera.update_view_matrix()
        light_list = list(filter(lambda x: isinstance(x, Light), descendant_list))

        # Separate opaque and transparent meshes
        opaque_meshes = []
        transparent_meshes = []
        for mesh in mesh_list:
            opacity_uniform = mesh.material.uniform_dict.get("opacity", None)
            if opacity_uniform and opacity_uniform.data < 1.0:
                transparent_meshes.append(mesh)
            else:
                opaque_meshes.append(mesh)

        # --- Render opaque meshes ---
        for mesh in opaque_meshes:
            if not mesh.visible:
                continue
            GL.glUseProgram(mesh.material.program_ref)
            GL.glBindVertexArray(mesh.vao_ref)

            mesh.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
            mesh.material.uniform_dict["viewMatrix"].data = camera.view_matrix
            mesh.material.uniform_dict["projectionMatrix"].data = camera.projection_matrix

            if "viewPosition" in mesh.material.uniform_dict:
                mesh.material.uniform_dict["viewPosition"].data = camera.global_position
            if self._shadows_enabled and "shadow0" in mesh.material.uniform_dict:
                mesh.material.uniform_dict["shadow0"].data = self._shadow_object
            if "light0" in mesh.material.uniform_dict:
                for i, light in enumerate(light_list):
                    key = f"light{i}"
                    if key in mesh.material.uniform_dict:
                        mesh.material.uniform_dict[key].data = light

            for uniform in mesh.material.uniform_dict.values():
                uniform.upload_data()

            mesh.material.update_render_settings()
            GL.glDrawArrays(mesh.material.setting_dict["drawStyle"], 0, mesh.geometry.vertex_count)

        # --- Render transparent meshes ---
        transparent_meshes.sort(
            key=lambda m: np.sum((np.array(m.global_position) - np.array(camera.global_position)) ** 2),
            reverse=True
        )

        GL.glDepthMask(GL.GL_FALSE)  # Disable writing to depth buffer

        for mesh in transparent_meshes:
            if not mesh.visible:
                continue
            GL.glUseProgram(mesh.material.program_ref)
            GL.glBindVertexArray(mesh.vao_ref)

            mesh.material.uniform_dict["modelMatrix"].data = mesh.global_matrix
            mesh.material.uniform_dict["viewMatrix"].data = camera.view_matrix
            mesh.material.uniform_dict["projectionMatrix"].data = camera.projection_matrix

            if "viewPosition" in mesh.material.uniform_dict:
                mesh.material.uniform_dict["viewPosition"].data = camera.global_position
            if self._shadows_enabled and "shadow0" in mesh.material.uniform_dict:
                mesh.material.uniform_dict["shadow0"].data = self._shadow_object
            if "light0" in mesh.material.uniform_dict:
                for i, light in enumerate(light_list):
                    key = f"light{i}"
                    if key in mesh.material.uniform_dict:
                        mesh.material.uniform_dict[key].data = light

            for uniform in mesh.material.uniform_dict.values():
                uniform.upload_data()

            mesh.material.update_render_settings()
            GL.glDrawArrays(mesh.material.setting_dict["drawStyle"], 0, mesh.geometry.vertex_count)

        GL.glDepthMask(GL.GL_TRUE)  # Re-enable writing to depth buffer

    def enable_shadows(self, shadow_light, strength=0.5, resolution=(512, 512)):
        self._shadows_enabled = True
        self._shadow_object = Shadow(shadow_light, strength=strength, resolution=resolution)
