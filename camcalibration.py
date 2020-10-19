## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

###############################################
##      Open CV and Numpy integration        ##
###############################################
# Resources:
# Intrinsic Parameters-  Resource[1] 
# ('https://bit.ly/3nQTprF')
#Intrinsic Parameters- Main one to develop code[2] 
#('https://bit.ly/3j034bX')
# Camera Calibration [3]
#'https://nikatsanka.github.io/camera-calibration-using-opencv-and-python.html'




import pyrealsense2 as rs
import numpy as np
import cv2
import glob
import keyboard 

# removed testing
dirpath= r'C:\Users\karla\OneDrive\Documents\GitHub\KUL_Thesis'
#squaresize is in meters

#def drawchessboard(dirpath, prefix='Image', image_format='png',width,height,squaresize):
def drawchessboard(square_size, width, height,dirpath, prefix, image_format):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((width*height,3), np.float32)
    objp[:,:2] = np.mgrid[0:width,0:height].T.reshape(-1,2)

    objp = objp * square_size 

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    stat_images = glob.glob(dirpath+'/' + prefix + '*.' + image_format)
    
    #Start counter for images used
    found_img=0
    for fname in stat_images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (width,height),None)

        # If found, add object points, image points (after refining them)
        if ret == True: #ret or retval is a variable used to assign the status of the last executed command to the retval variable
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)
            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (width,height), corners2,ret)
            found_img+=1 # count +1 when corneres are found in each frame
            
            cv2.imshow ('Image', img)
            cv2.waitKey(500)
        
    print("Number of images used for calibration: ", found_img)
    cv2.destroyAllWindows()
    #Calibration
    # Get camera matrix, distortion coefficients, rotation and translation vector.  
    rms, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    
    #undistort
    undistort(stat_imgages,mtx,dist)
    return [rms, mtx, dist, rvecs, tvecs]

    #cv2.destroyAllWindows()

def save_coefficients(mtx, dist, path):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", mtx)
    cv_file.write("D", dist)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()

def undistort(stat_imgages,mtx,dist):
    count=1
    for fname in images:
        img = cv2.imread(fname)
        h,w=image.shape[:2]
        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        
        # crop the image
        x,y,w,h = roi
        dst = dst[y:y+h, x:x+w]
        countstr=str(countstr)
        cv2.imwrite('calibresult'+countstr+'.png',dst)
        count+=1

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
fps=30
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, fps)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, fps)

# Start streaming
pipeline.start(config)

try:
    
    while True:

        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        ##depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # Stack both images horizontally
       #images = np.hstack((color_image, depth_colormap))
        images = color_image
        
        # Show images
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        cv2.waitKey(5)
        
        #Capture image
        count=0
        #cv2.waitKey(1)
        print("Press 'y'  To begin capturing images ")

        while keyboard.is_pressed('y'):
            status=input("Get into frame.\n Press 'Enter' to capture the image")
            if keyboard.wait('Enter'):
                count+=1
                cv2.waitKey(2)
                cap_img=cv2.imwrite('Image'+str(count)+'.png', images)
                print("Image has been captured")
                cv2.waitKey(5)
                status=input("Press Enter if you wish to continue.")
                cv2.waitKey(5)
            else:
                break
        print('The number of images captures',  count)
        
        #Include an exit key
        #if KeyboardInterrupt:
        if keyboard.wait('esc'):
            break
except:
  print("An exception occurred")  
        
finally:
    # Stop streaming
    pipeline.stop()
    print("Pipeline has been stopped")
    

######################################################################################
# EXECUTE CALIBRATION
#######################################################################################

#Get cameracalibration   
squaresize =0.024
width=9
height=7
image_format='png'
prefix='Image'
rms, mtx, dist, rvecs, tvecs= drawchessboard(square_size, width, height,dirpath, prefix, image_format)

# Save coefficients
#save_coefficients(mtx, dist, dirthpath):