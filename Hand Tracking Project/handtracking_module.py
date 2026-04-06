import cv2 as cv
import mediapipe as mp
import time

cap = cv.VideoCapture(0) # my webcam 

# our class
class handDetector():
    def __init__(self ,mode = False , maxHands = 2 , detectionCon = 0.5 , trackCon = 0.5 ) :
        self.mode = mode  # self.mode = mode  => the object can have its own variable and this 'self.mode' is that varible , i.e when ever we will use the variable of the object then we will call it self.something , and initially we are assigning it a value provided by the user  and we are calling it mode and we are providing it the value of the mode i.e False 
        # and same thing we have to do with other params 
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        # without self these are just temperory variables and gets lost after init and not usable at all 
        # while with self these become an object variable/property and becomes available everywhere 
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        

    def findHands(self ,img , draw = True): #we will need an image to find the hand's image  , setting initial flag for drawing as True so that we can decide 
        # sending the rgb image : this Hands class only takes RGB images for it to detect the landmarkers 
        imgRGB = cv.cvtColor(img , cv.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks) # to check if any thing is detected or not 

        if hasattr(self, "results") and self.results.multi_hand_landmarks:
            # here we are getting for all hands 
            for handLandmarks in self.results.multi_hand_landmarks:
                # getting the id(index) number and landmark information(the x and y coordinates
                
                if draw: #i.e we are checking if we need to draw or not 
                    self.mpDraw.draw_landmarks(img, handLandmarks , self.mpHands.HAND_CONNECTIONS) 
        return img  
    
    def findPosition(self , img, handNo = 0 , draw =True) :
        lmList = []
        # now we are going to check if any landmark were detected or not .
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo] # i.e out of all the hands we have pointed it to a particular hand number 
            # and within that hand it will get all the landmarks and put them in a list 
            for id , lm in enumerate(myHand.landmark):
                # so now here we need to specify which hand are we talking about 
                h, w, c = img.shape
                # finding the centre positions of lms 
                cx , cy = int(lm.x*w) , int(lm.y*h)
                # print(id , cx , cy) # i.e the id or lm and where it is located (cx ,cy)
                lmList.append([id , cx ,cy])

                if draw:# i.e for the first landmark 
                     cv.circle(img , (cx ,cy) , 5 , (255 , 0 , 255) , cv.FILLED)

        return lmList

def main():
    #  now we are going to put our while loop inside it 
    pTime = 0 # previous time 
    cTime = 0 # current time 
    cap = cv.VideoCapture(0) # my webcam 
    detector = handDetector() # here we are not giving any parameters bcz we are already giving the default params above 

    while True:
        success, img = cap.read()

        if not success:
            print("Camera not working")
            break
        img = detector.findHands(img) # since from above code part , we have findHands as a method of the object 


        lmlist = detector.findPosition(img) # since it will give us a list
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


# making it Modular 
if __name__ == '__main__' : # i.e if we are running this script of 'main' i.e the entire above code part which is inside the main functin then do the below i.e run the code 
     main() # so whatever we will write in the main part will be like a dummy code to showcase what can this module do 