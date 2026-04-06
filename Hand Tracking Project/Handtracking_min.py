import cv2 as cv
import mediapipe as mp
import time

cap = cv.VideoCapture(0) # my webcam 

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

pTime = 0 # previous time 
cTime = 0 # current time 


while True:
    success , img =  cap.read()
    # sending the rgb image : this Hands class only takes RGB images for it to detect the landmarkers 
    imgRGB = cv.cvtColor(img , cv.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks) # to check if any thing is detected or not 

    if results.multi_hand_landmarks:
        for handLandmarks in results.multi_hand_landmarks:
            # getting the id(index) number and landmark information(the x and y coordinates)
            for id , lm in enumerate(handLandmarks.landmark):
                # print(id , lm)
            # multiplying with the width and the height to get the pixel values 
                h, w, c = img.shape
                # finding the centre positions of lms 
                cx , cy = int(lm.x*w) , int(lm.y*h)
                print(id , cx , cy) # i.e the id or lm and where it is located (cx ,cy)

                if id == 0:# i.e for the first landmark 
                     cv.circle(img , (cx ,cy) , 25 , (255 , 0 , 255) , cv.FILLED) #i.e a radius of 25 for the point where we are keeping it as id == 0 , and similary we can check for other id's or markers at different locations 

            mpDraw.draw_landmarks(img, handLandmarks , mpHands.HAND_CONNECTIONS) 
            # handLandmarks => it will draw the landmarkers(pointers / joints) in the hand/fingers 
            # mpHands.HAND_CONNECTIONS => it will draw the connections between landmarkers
            # we get all the 21 landmarks

    # showing the fps
    cTime = time.time()
    fps = 1/(cTime - pTime)
    pTime = cTime
    # displying
    cv.putText(img , str(int(fps)) , (10 , 70) , cv.FONT_HERSHEY_COMPLEX , 3 , (255,0,255) ,3 ) # 3 : scale , 3 : thickness 


    if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cv.imshow('Image' , img)
    cv.waitKey(1)# => Continuous video loop ✅ allows the script to continue publishing the video almost immediately if no key is detected.
    # for waitkey(0)  => Pause until key press ❌ video will stop and won't run unless any key is pressed 