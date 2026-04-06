import cv2 as cv
import mediapipe as mp
import time
import handtracking_module as htm



pTime = 0 
cTime = 0  
cap = cv.VideoCapture(0) # my webcam 
detector = htm.handDetector() # i.e using the htm module 

while True:
    success, img = cap.read()

    if not success:
        print("Camera not working")
        break
    img = detector.findHands(img) # since from above code part , we have findHands as a method of the object 
    lmlist = detector.findPosition(img , draw = False) # since it will give us a list
    if len(lmlist)!= 0 :
        print(lmlist[4]) 


    cTime = time.time()
    fps = 1/(cTime - pTime)
    pTime = cTime
    # displying
    cv.putText(img , str(int(fps)) , (10 , 70) , cv.FONT_HERSHEY_COMPLEX , 3 , (255,0,255) ,3 ) # 3 : scale , 3 : thickness 


    if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cv.imshow('Image' , img)