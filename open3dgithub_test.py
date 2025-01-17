# Open3D: www.open3d.org
# The MIT License (MIT)
# See license file or visit www.open3d.org for details

# examples/python/reconstruction_system/sensors/realsense_pcd_visualizer.py

# pyrealsense2 is required.
# Please see instructions in https://github.com/IntelRealSense/librealsense/tree/master/wrappers/python

# Based off: https://github.com/intel-isl/Open3D/blob/master/examples/python/reconstruction_system/sensors/realsense_pcd_visualizer.py
###################################################################################

#### 
# Final implementation
# Estimate ~20fps

####

import pyrealsense2 as rs
import numpy as np
from enum import IntEnum

from datetime import datetime
import open3d as o3d


class Preset(IntEnum):
    Custom = 0
    Default = 1
    Hand = 2
    HighAccuracy = 3
    HighDensity = 4
    MediumDensity = 5


def get_intrinsic_matrix(frame):
    intrinsics = frame.profile.as_video_stream_profile().intrinsics
    out = o3d.camera.PinholeCameraIntrinsic(640, 480, intrinsics.fx,
                                            intrinsics.fy, intrinsics.ppx,
                                            intrinsics.ppy)
    return out


if __name__ == "__main__":

    # Create a pipeline
    pipeline = rs.pipeline()

    #Create a config and configure the pipeline to stream
    #  different resolutions of color and depth streams
    config = rs.config()

    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

    # Start streaming
    profile = pipeline.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()

    # Using preset HighAccuracy for recording
    depth_sensor.set_option(rs.option.visual_preset, Preset.HighAccuracy)
    #The “High Accuracy” preset will impose stricter criteria, and will only provide those depth
    #values that are generated with very high confidence. This will give a less dense depth map
    #in general but is very good for autonomous robots where false depth, aka. Hallucinations,
    #are much worse than no depth. 
    
    
    #KR Turn ON Emitter
    depth_sensor.set_option(rs.option.emitter_always_on, 1)

    # Get depth sensor's depth scale 
    depth_scale = depth_sensor.get_depth_scale()

    # We will not display the background of objects more than
    #  clipping_distance_in_meters meters away
    clipping_distance_in_meters = 3  # 3 meter
    clipping_distance = clipping_distance_in_meters / depth_scale
    

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames. Here RGB.
    align_to = rs.stream.color
    align = rs.align(align_to)
    
    #initialize visualizer
    vis = o3d.visualization.Visualizer()
    vis.create_window()

    pcd = o3d.geometry.PointCloud()
    flip_transform = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]

    # Streaming loop
    frame_count = 0
    #frame_count= False
    try:
        while True:

            dt0 = datetime.now()

            # Get frameset of color and depth
            frames = pipeline.wait_for_frames()

            # Align the depth frame to color frame
            aligned_frames = align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            intrinsic = o3d.camera.PinholeCameraIntrinsic(get_intrinsic_matrix(color_frame))

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue
            
            #Numpy array equivalent
            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            depth_od3 = o3d.geometry.Image(depth_image)
            color_temp_od3 = o3d.geometry.Image(color_image)
            
            """
            depth_img = o3d.geometry.Image(
                np.array(aligned_depth_frame.get_data()))
            color_temp = np.asarray(color_frame.get_data())
            color_image = o3d.geometry.Image(color_temp)
            """
            rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                color_temp_od3,
                depth_od3,
                depth_scale=1.0 / depth_scale,
                depth_trunc=clipping_distance_in_meters,
                convert_rgb_to_intensity=False)
            
            temp = o3d.geometry.PointCloud.create_from_rgbd_image(
                rgbd_image, intrinsic)
            temp.transform(flip_transform)
            pcd.points = temp.points
            pcd.colors = temp.colors

            if frame_count == 0:
                #if frame_count== False:
                vis.add_geometry(pcd)

            vis.update_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

            process_time = datetime.now() - dt0
            print("FPS: " + str(1 / process_time.total_seconds()))
            frame_count += 1
            #frame_count=True

    finally:
        pipeline.stop()
    vis.destroy_window()
