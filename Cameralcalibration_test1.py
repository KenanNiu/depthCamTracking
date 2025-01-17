############## Camera Calibration##########################

#purpose: Obtain intrnsic camera parameters 

# Resources:
# Intrinsic Parameters-  Resource[1] 
# ('https://bit.ly/3nQTprF')
#Intrinsic Parameters- [2] 
#https: // medium.com/@aliyasineser/opencv-camera-calibration-e9a48bdd1844
#==> His code was developed based Open CV tutorial [4] but structures it in the calibration and save coefficients format
#other wise used his structure
# Camera Calibration [3]
#'https://nikatsanka.github.io/camera-calibration-using-opencv-and-python.html'
#OpenCVPtyhon Tutorials: Camera Calibration and 3D Reconstruction*** MAIN ONE TO DEVELOP CODE [4]
#'https://docs.opencv.org/master/dc/dbb/tutorial_py_calibration.html'

#('https://bit.ly/3j034bX') ??

import pyrealsense2 as rs
import numpy as np
import cv2
import glob
import keyboard 


def drawchessboard(square_size, width, height,dirpath2, prefix, image_format):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # prepares object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((width*height,3), np.float32)
    objp[:,:2] = np.mgrid[0:width,0:height].T.reshape(-1,2)

    objp = objp * square_size 

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    stat_images = glob.glob(dirpath2+'/' + prefix + '*.' + image_format)
    ##print(len(stat_images))
    #Start counter for images used
    found_img=0
    for fname in stat_images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (width, height), None)
        print(ret)

        # If found, add object points, image points (after refining them)
        if ret == True: #ret or retval is a variable used to assign the status of the last executed command to the retval variable
            objpoints.append(objp)
            
            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)
            
            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (width, height), corners2, ret)
            found_img+=1 # count +1 when corneres are found in each frame
            
            cv2.imshow ('Image', img)
            cv2.waitKey(500)
        
    print("Number of images used for calibration: ", found_img)
    cv2.destroyAllWindows()
    #Calibration
    
    # Get camera matrix, distortion coefficients, rotation and translation vector.  
    rms, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    
    
    print("---------GOT THE CAMER PARAMETERS!-------------")
    #undistort (Added 28.10.2020)
    #undistort(stat_images,mtx,dist)
    
    
    #210724 add  error calc
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
        mean_error += error
    #print( "total error: {}".format(mean_error/len(objpoints)) )
    print("total error", mean_error/len(objpoints))
    
    return [rms, mtx, dist, rvecs, tvecs, stat_images]

    #cv2.destroyAllWindows()

def save_coefficients(mtx, dist, rvecs,tvecs, dirpath2):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    cv_file = cv2.FileStorage(dirpath2+'/'+'calibration210731.txt', cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", mtx)
    cv_file.write("D", dist)
    cv_file.write("R", rvecs)
    cv_file.write("t", tvecs)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()

def undistort(stat_images,mtx,dist):
    count=1
    for fname in stat_images:
        img = cv2.imread(fname)
        #3 Get dimensions of image: get width and heigh
        h,w=img.shape[:2] 
        
        ### overview of parameters
        #ROI: Rectongular region of interest in Open CV
        # cv.getOptimalNewCameraMatrix(	cameraMatrix, distCoeffs, imageSize, alpha[, newImgSize[, centerPrincipalPoint]])
        #alpha=1 when all the source image pixels are retained in the undistorted image). See stereoRectify for details.
        #alpha=1 means that the rectified image is decimated and shifted so that all the pixels from the original images 
        # from the cameras are retained in the rectified images (no source image pixels are lost). Any intermediate value yields an intermediate result between those two extreme cases.

        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))
        
        #undistort 
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        
        #crop the image
        
        #x,y are top left coordinates / #y+h are the bottom left coordinates / #x+w are the top right coordinates
        #Define the ROI 
        x,y,w,h = roi
        #crop image to only the specified bounds 
        dst = dst[y:y+h, x:x+w]
        countstr=str(count)
        cv2.imwrite('calibresult'+countstr+'.png',dst)
        count+=1


#Initialize directory path

#First calibration
#dirpath = r'C:\Users\karla\OneDrive\Documents\GitHub\KUL_Thesis'

#second calibration. Make sure to update path directory when calling coefficients
#dirpath = r'C:\Users\karla\OneDrive\Documents\GitHub\KUL_Thesis'
dirpath2 = r'D:\Thesis Absolete Folders\Calibration Images'


"""# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
fps=30
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, fps)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, fps)
#Initiate a counter for the number of images captured
count=0
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
        

        images = color_image
        
        # Show images
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        cv2.waitKey(1)
   
        #Enter to begin capturing images
        if keyboard.is_pressed('Enter'):
            count+=1
            cap_img=cv2.imwrite('Image'+str(count)+'.png', images)
            print("Image has been captured.")
            #proceed=input()
            continue 
              
        #ESC to exit video stream at any time
        if keyboard.is_pressed('esc'):
            break
    
except:
  print("An exception occurred")  
        
finally:
    # Stop streaming
    pipeline.stop()
    print("Pipeline has been stopped")
    print('Count images',  count)
    """

######################################################################################
# EXECUTE CALIBRATION
#######################################################################################

#Get cameracalibration   
square_size =0.024
width=8
height=6
image_format='png'
prefix='Image'
rms, mtx, dist, rvecs, tvecs, stat_images= drawchessboard(square_size, width, height,dirpath2, prefix, image_format)

#Save coefficients
#save_coefficients(mtx, dist, dirpath2)
save_coefficients(mtx, dist, rvecs, tvecs, dirpath2)
