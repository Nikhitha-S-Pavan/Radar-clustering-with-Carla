#!/usr/bin/env python

# Copyright (c) 2019 Aptiv
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
An example of client-side bounding boxes with basic car controls.
Controls:
    W            : throttle
    S            : brake
    AD           : steer
    Space        : hand-brake
    ESC          : quit
"""

# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


import glob
import os
import sys
import math
import json
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import carla

import weakref
import random

try:
    import pygame
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_SPACE
    from pygame.locals import K_a
    from pygame.locals import K_d
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_RIGHT
    from pygame.locals import K_LEFT
    from pygame.locals import K_UP
    from pygame.locals import K_DOWN
    from pygame.locals import K_g

    from pygame.locals import K_q
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

VIEW_WIDTH = 1920//2
VIEW_HEIGHT = 1080//2
VIEW_FOV = 90

BB_COLOR = (248, 64, 24)

# ==============================================================================
# -- ClientSideBoundingBoxes ---------------------------------------------------
# ==============================================================================


class ClientSideBoundingBoxes(object):
    """
    This is a module responsible for creating 3D bounding boxes and drawing them
    client-side on pygame surface.
    """

    @staticmethod
    def get_bounding_boxes(vehicles, camera, timestamp):
        """
        Creates 3D bounding boxes based on carla vehicle list and camera.
        """




        bounding_boxes = [ClientSideBoundingBoxes.get_bounding_box(vehicle, camera, timestamp) for vehicle in vehicles]

        # filter objects behind camera
        bounding_boxes = [bb for bb in bounding_boxes if all(bb[:, 2] > 0)]
        return bounding_boxes

    @staticmethod
    def draw_bounding_boxes( display, bounding_boxes):
        """
        Draws bounding boxes on pygame display.
        """


        bb_surface = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
        bb_surface.set_colorkey((0, 0, 0))
        for bbox in bounding_boxes:
            points = [(int(bbox[i, 0]), int(bbox[i, 1])) for i in range(8)]
            # draw lines
            # base
            pygame.draw.line(bb_surface, BB_COLOR, points[0], points[1])
            pygame.draw.line(bb_surface, BB_COLOR, points[0], points[1])
            pygame.draw.line(bb_surface, BB_COLOR, points[1], points[2])
            pygame.draw.line(bb_surface, BB_COLOR, points[2], points[3])
            pygame.draw.line(bb_surface, BB_COLOR, points[3], points[0])
            # top
            pygame.draw.line(bb_surface, BB_COLOR, points[4], points[5])
            pygame.draw.line(bb_surface, BB_COLOR, points[5], points[6])
            pygame.draw.line(bb_surface, BB_COLOR, points[6], points[7])
            pygame.draw.line(bb_surface, BB_COLOR, points[7], points[4])
            # base-top
            pygame.draw.line(bb_surface, BB_COLOR, points[0], points[4])
            pygame.draw.line(bb_surface, BB_COLOR, points[1], points[5])
            pygame.draw.line(bb_surface, BB_COLOR, points[2], points[6])
            pygame.draw.line(bb_surface, BB_COLOR, points[3], points[7])
        display.blit(bb_surface, (0, 0))

    @staticmethod
    def get_bounding_box(vehicle, camera, timestamp):
        """
        Returns 3D bounding box for a vehicle based on camera view.
        """



        bb_cords = ClientSideBoundingBoxes._create_bb_points(vehicle, timestamp)
        cords_x_y_z = ClientSideBoundingBoxes._vehicle_to_sensor(bb_cords, vehicle, camera)[:3, :]
        cords_y_minus_z_x = np.concatenate([cords_x_y_z[1, :], -cords_x_y_z[2, :], cords_x_y_z[0, :]])
        bbox = np.transpose(np.dot(camera.calibration, cords_y_minus_z_x))
        camera_bbox = np.concatenate([bbox[:, 0] / bbox[:, 2], bbox[:, 1] / bbox[:, 2], bbox[:, 2]], axis=1)
        return camera_bbox

    def get_id(label_name):
        if label_name == "autopilot":
            label_id = 1
        if label_name == "pedestrian":
            label_id = 2
        else:
            label_id = 0
        return label_id

    @staticmethod
    def _create_bb_points(vehicle, timestamp):
        """
        Returns 3D bounding box for a vehicle.
        """
        """get_vehicle = vehicle.get_world()
        world_snapshot = get_vehicle.get_snapshot()
        timestamp = world_snapshot.timestamp"""
        arr = {}
        cords = np.zeros((8, 4))
        location = vehicle.get_transform().location
        extent = vehicle.bounding_box.extent
        data = [location.x, location.y, location.z]
        #print(data, timestamp.frame, "+++++++++++")
        arr["boxloc"] = data
        label_name = vehicle.attributes["role_name"]
        label_id = ClientSideBoundingBoxes.get_id(label_name)
        arr["label_id"] = label_id
        arr["frame_id"] = timestamp.frame
        with open('C:\\Users\\NIU2KOR\\Desktop\\CARLA_0.9.8\\WindowsNoEditor\\PythonAPI\\examples\\box.json', 'a+', newline='') as fp:
            json.dump(arr, fp)
            fp.write('\n')
        cords[0, :] = np.array([extent.x, extent.y, -extent.z, 1])
        cords[1, :] = np.array([-extent.x, extent.y, -extent.z, 1])
        cords[2, :] = np.array([-extent.x, -extent.y, -extent.z, 1])
        cords[3, :] = np.array([extent.x, -extent.y, -extent.z, 1])
        cords[4, :] = np.array([extent.x, extent.y, extent.z, 1])
        cords[5, :] = np.array([-extent.x, extent.y, extent.z, 1])
        cords[6, :] = np.array([-extent.x, -extent.y, extent.z, 1])
        cords[7, :] = np.array([extent.x, -extent.y, extent.z, 1])


        return cords



    @staticmethod
    def _vehicle_to_sensor(cords, vehicle, sensor):
        """
        Transforms coordinates of a vehicle bounding box to sensor.
        """

        world_cord = ClientSideBoundingBoxes._vehicle_to_world(cords, vehicle)
        sensor_cord = ClientSideBoundingBoxes._world_to_sensor(world_cord, sensor)
        return sensor_cord

    @staticmethod
    def _vehicle_to_world(cords, vehicle):
        """
        Transforms coordinates of a vehicle bounding box to world.
        """

        bb_transform = carla.Transform(vehicle.bounding_box.location)

        bb_vehicle_matrix = ClientSideBoundingBoxes.get_matrix(bb_transform)

        vehicle_world_matrix = ClientSideBoundingBoxes.get_matrix(vehicle.get_transform())

        bb_world_matrix = np.dot(vehicle_world_matrix, bb_vehicle_matrix)

        world_cords = np.dot(bb_world_matrix, np.transpose(cords))
        return world_cords

    @staticmethod
    def _world_to_sensor(cords, sensor):
        """
        Transforms world coordinates to sensor.
        """

        sensor_world_matrix = ClientSideBoundingBoxes.get_matrix(sensor.get_transform())
        world_sensor_matrix = np.linalg.inv(sensor_world_matrix)
        sensor_cords = np.dot(world_sensor_matrix, cords)
        return sensor_cords

    @staticmethod
    def get_matrix(transform):
        """
        Creates matrix from carla transform.
        """
        box_arr = {}
        rotation = transform.rotation
        location = transform.location
        box_array= [location.x, location.y, location.z]
        box_arr["box"] = box_array
        c_y = np.cos(np.radians(rotation.yaw))
        s_y = np.sin(np.radians(rotation.yaw))
        c_r = np.cos(np.radians(rotation.roll))
        s_r = np.sin(np.radians(rotation.roll))
        c_p = np.cos(np.radians(rotation.pitch))
        s_p = np.sin(np.radians(rotation.pitch))
        matrix = np.matrix(np.identity(4))
        matrix[0, 3] = location.x
        matrix[1, 3] = location.y
        matrix[2, 3] = location.z
        matrix[0, 0] = c_p * c_y
        matrix[0, 1] = c_y * s_p * s_r - s_y * c_r
        matrix[0, 2] = -c_y * s_p * c_r - s_y * s_r
        matrix[1, 0] = s_y * c_p
        matrix[1, 1] = s_y * s_p * s_r + c_y * c_r
        matrix[1, 2] = -s_y * s_p * c_r + c_y * s_r
        matrix[2, 0] = s_p
        matrix[2, 1] = -c_p * s_r
        matrix[2, 2] = c_p * c_r
        return matrix



# ==============================================================================
# -- BasicSynchronousClient ----------------------------------------------------
# ==============================================================================


class BasicSynchronousClient(object):
    """
    Basic implementation of a synchronous client.
    """

    def __init__(self):
        self.client = None
        self.world = None
        self.camera = None
        self.car = None
        self.radar = None

        self.display = None
        self.image = None
        self.capture = True
        self.velocity_range = 7.5  # m/s

    def camera_blueprint(self):
        """
        Returns camera blueprint.
        """

        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', str(VIEW_WIDTH))
        camera_bp.set_attribute('image_size_y', str(VIEW_HEIGHT))
        camera_bp.set_attribute('fov', str(VIEW_FOV))
        return camera_bp

    def radar_blueprint(self):
        bp = self.world.get_blueprint_library().find('sensor.other.radar')
        bp.set_attribute('horizontal_fov', str(35))
        bp.set_attribute('vertical_fov', str(20))
        return bp

    def set_synchronous_mode(self, synchronous_mode):
        """
        Sets synchronous mode.
        """

        settings = self.world.get_settings()
        settings.synchronous_mode = synchronous_mode
        self.world.apply_settings(settings)

    def setup_car(self):
        """
        Spawns actor-vehicle to be controled.
        """

        car_bp = self.world.get_blueprint_library().filter('vehicle.*')[0]
        #print(car_bp)
        location = random.choice(self.world.get_map().get_spawn_points())
        self.car = self.world.spawn_actor(car_bp, location)

    def setup_camera(self,  vehicles):
        """
        Spawns actor-camera to be used to render view.
        Sets calibration for client-side boxes rendering.
        """
        for vehicle in vehicles:
            get_vehicle = vehicle.get_world()
            world_snapshot = get_vehicle.get_snapshot()
            timestamp = world_snapshot.timestamp

            camera_transform = carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15))
            self.camera = self.world.spawn_actor(self.camera_blueprint(), camera_transform, attach_to=self.car)
            weak_self = weakref.ref(self)
            self.camera.listen(lambda image: weak_self().set_image(weak_self, image))

            calibration = np.identity(3)
            calibration[0, 2] = VIEW_WIDTH / 2.0
            calibration[1, 2] = VIEW_HEIGHT / 2.0
            calibration[0, 0] = calibration[1, 1] = VIEW_WIDTH / (2.0 * np.tan(VIEW_FOV * np.pi / 360.0))
            self.camera.calibration = calibration


    def setup_radar(self, world, display):

        world_snapshot = world.get_snapshot()
        timestamp = world_snapshot.timestamp
        for actor_snapshot in world_snapshot:  # Get the actor and the snapshot information
            actual_actor = world.get_actor(actor_snapshot.id)

            actor_snapshot.get_transform()
            actor_snapshot.get_velocity()
            actor_snapshot.get_angular_velocity()
            actor_snapshot.get_acceleration()


        self.radar = self.world.spawn_actor(
            self.radar_blueprint(),
            carla.Transform(
                carla.Location(x=2.8, z=1.0),
                carla.Rotation(pitch=5)),
            attach_to=self.car)
        weak_self = weakref.ref(self)
        self.radar.listen(
            lambda radar_data: BasicSynchronousClient._Radar_callback(weak_self, radar_data, timestamp, world, display))

    @staticmethod
    def _Radar_callback(weak_self, radar_data, timestamp, world, display):
        self = weak_self()
        array_value = {}
        if not self:
            return
        # To get a numpy [[vel, altitude, azimuth, depth],...[,,,]]:
        points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (len(radar_data), 4))


        current_rot = radar_data.transform.rotation
        current_loc = radar_data.transform.location
        loc_arr = [current_loc.x, current_loc.y, current_loc.z]




        for detect in radar_data:
            azi = math.degrees(detect.azimuth)
            alt = math.degrees(detect.altitude)
            # The 0.25 adjusts a bit the distance so the dots can
            # be properly seen
            fw_vec = carla.Vector3D(x=detect.depth - 0.25)
            carla.Transform(
                carla.Location(),
                carla.Rotation(
                    pitch=current_rot.pitch + alt,
                    yaw=current_rot.yaw + azi,
                    roll=current_rot.roll)).transform(fw_vec)

            def clamp(min_v, max_v, value):
                return max(min_v, min(value, max_v))

            norm_velocity = detect.velocity / self.velocity_range  # range [-1, 1]
            r = int(clamp(0.0, 1.0, 1.0 - norm_velocity) * 255.0)
            g = int(clamp(0.0, 1.0, 1.0 - abs(norm_velocity)) * 255.0)
            b = int(abs(clamp(- 1.0, 0.0, - 1.0 - norm_velocity)) * 255.0)
            self.world.debug.draw_point(
                radar_data.transform.location + fw_vec,
                size=0.075,
                life_time=0.06,
                persistent_lines=False,
                color=carla.Color(r, g, b))
            loc_arr = [radar_data.transform.location.x , radar_data.transform.location.y, radar_data.transform.location.z]

            array_value["loc_arr"] = loc_arr
            array_value["frame_id"] = timestamp.frame
            print(loc_arr, timestamp.frame)
            with open('C:\\Users\\NIU2KOR\\Desktop\\CARLA_0.9.8\\WindowsNoEditor\\PythonAPI\\examples\\point.json',
                      'a+', newline='') as fp:
                json.dump(array_value, fp)
                fp.write('\n')

    def toggle_radar(self):
        if self.radar is None:
            self.radar = BasicSynchronousClient.setup_radar(self.vehicle)
        """elif self.radar_sensor.sensor is not None:
            self.radar_sensor.sensor.destroy()
            self.radar_sensor = None"""

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

    def control(self, car):
        """
        Applies control to main car based on pygame pressed keys.
        Will return True If ESCAPE is hit, otherwise False to end main loop.
        """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                if event.key == K_g:
                    self.toggle_radar()

        keys = pygame.key.get_pressed()
        if keys[K_ESCAPE]:
            return True

        control = car.get_control()
        control.throttle = 0
        if keys[K_w]:
            control.throttle = 1
            control.reverse = False
        elif keys[K_s]:
            control.throttle = 1
            control.reverse = True

        if keys[K_a]:
            control.steer = max(-1., min(control.steer - 0.05, 0))
        elif keys[K_d]:
            control.steer = min(1., max(control.steer + 0.05, 0))
        else:
            control.steer = 0
        control.hand_brake = keys[K_SPACE]

        car.apply_control(control)
        return False

    @staticmethod
    def set_image(weak_self, img):
        """
        Sets image coming from camera sensor.
        The self.capture flag is a mean of synchronization - once the flag is
        set, next coming image will be stored.
        """

        self = weak_self()
        if self.capture:
            self.image = img
            self.capture = False

    def render(self, display):
        """
        Transforms image from camera sensor and blits it to main pygame display.
        """

        if self.image is not None:
            array = np.frombuffer(self.image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (self.image.height, self.image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
            display.blit(surface, (0, 0))

    def game_loop(self):
        """
        Main program loop.
        """

        try:
            pygame.init()

            self.client = carla.Client('127.0.0.1', 2000)
            self.client.set_timeout(2.0)
            self.world = self.client.get_world()
            world_snapshot = self.world.get_snapshot()
            self.timestamp = world_snapshot.timestamp

            timestamp = self.timestamp
            self.set_up_car = self.client.get_world()
            world_snapshot = self.set_up_car.get_snapshot()
            self.timestamp = world_snapshot.timestamp
            self.setup_car()


            self.display = pygame.display.set_mode((VIEW_WIDTH, VIEW_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
            pygame_clock = pygame.time.Clock()

            self.set_synchronous_mode(True)

            vehicles = self.world.get_actors().filter('vehicle.*')
            pedestrian = self.world.get_actors().filter('walker.pedestrian.*')

            self.setup_camera(vehicles)


            while True:
                self.world.tick()

                self.capture = True
                pygame_clock.tick_busy_loop(60)
                timestamp = self.timestamp


                self.render(self.display)
                bounding_boxes = ClientSideBoundingBoxes.get_bounding_boxes(vehicles, self.camera, timestamp)
                ClientSideBoundingBoxes.draw_bounding_boxes(self.display, bounding_boxes)


                bounding_boxes_walker = ClientSideBoundingBoxes.get_bounding_boxes(pedestrian, self.camera)

                ClientSideBoundingBoxes.draw_bounding_boxes(self.display, bounding_boxes_walker)
                BasicSynchronousClient.setup_radar(self, self.world, self.display)
                #BasicSynchronousClient.setup_radar(self, pedestrian)

                pygame.display.flip()

                pygame.event.pump()
                if self.control(self.car):
                    return

        finally:
            self.set_synchronous_mode(False)
            self.camera.destroy()
            self.car.destroy()
            pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    """
    Initializes the client-side bounding box demo.
    """

    try:
        client = BasicSynchronousClient()
        client.game_loop()
    finally:
        print('EXIT')


if __name__ == '__main__':
    main()