import os
import threading
import time
import numpy as np
import wx
import cv2
import pyautogui 
from pynput import keyboard, mouse
# from bing-image-downloader import downloader # TODO: implement new downloader

pyautogui.MINIMUM_DURATION = 0.01 # default: 0.1
pyautogui.MINIMUM_SLEEP = 0.05 # default: 0.05
pyautogui.PAUSE = 0.01 # default: 0.1

IMG_DEFAULT_SIZE = (600, 600)

class Image():
    def __init__(self, img_path, size=IMG_DEFAULT_SIZE):
        self.img = self.resize(cv2.imread(img_path), size)
        self.optThreshVal = 0
        self.threshVal = 0
        self.thresh = None
        self.contours = None
        self.contImg = None

        self.process()

    def resize(self, img, size):
        # resize img to fit in box size, preserving aspect ratio
        factor = self.resizeFactor(img.shape, size)
        return cv2.resize(img, None, fx=factor, fy=factor)
    
    def resizeFactor(self, oldDim, newDim):
        factor_y = newDim[0] / oldDim[0] 
        factor_x = newDim[1] / oldDim[1] 
        return min(factor_y, factor_x)
    
    def process(self):
        # make a guess at best threshVal and set
        div = 6
        chunk = 255/div
        scores = []
        for i in [chunk*x for x in range(div)]:
            self.setThresh(i)
            scores.append(self.contScore(self.contours))

        self.optThreshVal = int(chunk * scores.index(max(scores)))
        self.setThresh()

    def contScore(self, contours):
        # longer contours give a increase score, small ones decrease score
        # TODO - smarter contour scoring (adjust weight, stochastic hill climbing)
        score = 0
        for c in contours:
            if len(c) > 30:
                score += len(c)
            else:
                score -= len(c)
        return score

    def setThresh(self, newVal=None):
        # set threshold image, contours, and contour image
        if newVal:
            self.threshVal = newVal
        else:
            self.threshVal = self.optThreshVal

        imgray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(imgray, self.threshVal, 255, 0)
        self.thresh = thresh

        pad = 5 # pad the threshold to separate image contours from border
        vals, counts = np.unique(thresh[0,:], return_counts=True)
        mode = int(vals[np.argmax(counts)])
        paddedThresh = cv2.copyMakeBorder(thresh, pad, pad, pad, pad, cv2.BORDER_CONSTANT, None, mode)
        contours, _ = cv2.findContours(paddedThresh,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            contour[:,:,:] = contour[:,:,:] - pad
        self.contours = contours

        blackdrop = np.zeros((self.img.shape[0], self.img.shape[1],3), np.uint8)
        contImg = cv2.drawContours(blackdrop, contours, -1, (0,255,0), 1)
        self.contImg = contImg

    def getImg(self, size=None):
        if not size:
            return self.img
        return self.resize(self.img, size)
    
    def getThresh(self, val=None, size=None):
        if self.thresh:
            if not size:
                return self.thresh
            return self.resize(self.thresh, size)
        return None

    def getContours(self, size=None):
        if self.contours:
            if not size:
                return self.contours

            factor = self.resizeFactor(self.img.shape, size)
            scaled = tuple([np.copy(x) for x in self.contours]) # deep copy
            for contour in scaled:
                contour[:,:,0] = contour[:,:,0] * factor
                contour[:,:,1] = contour[:,:,1] * factor
            
            return scaled
        return None

    def getContImg(self, size=None):
        if self.contImg:
            if not size:
                return self.contImg
            return self.resize(self.contImg, size)
        return None

class Listener():

    def __init__(self, listType="keyboard"):
        self.key_pressed = False
        self.key = None
        self.key_listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
                )

        self.mouse_left_down = False
        self.mouse_listener = mouse.Listener(on_click=self.on_click)

        self.key_listener.start()
        self.mouse_listener.start()

    def on_press(self, key):
        self.key_pressed = True
        try:
            self.key = key.char
        except AttributeError:
            self.key = key # special keys don't have .char attribute

    def on_release(self, key):
        self.key_pressed = False
        self.key = None

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            self.mouse_left_down = True
        else:
            self.mouse_left_down = False

    def stop(self):
        self.key_listener.stop()
        self.mouse_listener.stop()


class Skribblr(wx.Frame):

    def __init__(self, parent, title, size=(1300, 1600)):
        super(Skribblr, self).__init__(parent, title=title)


        self.SetSize(*size)
        self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        
        self.InitUI()
        self.Centre()

        if not os.path.exists("./pics"):
            os.makedirs("./pics")

        self.imgs = []
        self.processImgs()
        self.displayImg()

        self.threads = [] #TODO thread management

        self.drawing = False;


    def InitUI(self):
        self.panel = wx.Panel(self)
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # prefix input box
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        prefix = wx.StaticText(self.panel, label='Type prefix here:')
        prefix.SetFont(font)
        hbox0.Add(prefix, flag=wx.RIGHT, border=8)
        self.tc0 = wx.TextCtrl(self.panel, id=wx.ID_ANY, value="clipart")
        hbox0.Add(self.tc0, proportion=1)
        vbox.Add(hbox0, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        vbox.Add((-1, 10))

        # query input box
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(self.panel, label='Get Images of:')
        st1.SetFont(font)
        hbox1.Add(st1, flag=wx.RIGHT, border=8)
        self.tc1 = wx.TextCtrl(self.panel, -1, style=wx.TE_PROCESS_ENTER)
        self.tc1.Bind(wx.EVT_TEXT_ENTER, self.downloadImgs)
        hbox1.Add(self.tc1, proportion=1)
        imgBut = wx.Button(self.panel, label="Go", size=(70,30))
        imgBut.Bind(wx.EVT_BUTTON, self.downloadImgs)
        hbox1.Add(imgBut)

        vbox.Add(hbox1, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add((-1, 10))

        # image select
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(self.panel, label='Select Image:')
        st2.SetFont(font)
        hbox2.Add(st2, flag=wx.RIGHT, border=8)

        leftBut = wx.Button(self.panel, label="<", size=(30,30))
        leftBut.Bind(wx.EVT_BUTTON, self.prevImg)
        hbox2.Add(leftBut)

        self.tc2 = wx.TextCtrl(self.panel, value="1", style=wx.TE_READONLY)
        hbox2.Add(self.tc2, proportion=1)

        rightBut = wx.Button(self.panel, label=">", size=(30,30))
        rightBut.Bind(wx.EVT_BUTTON, self.nextImg)
        hbox2.Add(rightBut)

        self.drawBut = wx.Button(self.panel, label="Start Draw!", size=(200,30))
        self.drawBut.Bind(wx.EVT_BUTTON, self.startDraw)
        hbox2.Add(self.drawBut)

        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        # image displayer
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.dispImg = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(wx.Image(*IMG_DEFAULT_SIZE[::-1])))
        hbox3.Add(self.dispImg)

        vbox.Add(hbox3, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 10))

        # slider
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sld = wx.Slider(self.panel, value=200, minValue=0, maxValue=255, size=(1000,1),
                        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)

        self.sld.Bind(wx.EVT_SCROLL_CHANGED, self.sliderChange)
        hbox4.Add(self.sld, flag=wx.ALL|wx.EXPAND, border=25)

        vbox.Add(hbox4, flag=wx.ALIGN_CENTRE|wx.CENTRE, border=10)

        self.panel.SetSizer(vbox)

    def processImgs(self):
        for imgName in os.listdir("./pics/")[1:]:
            try:
                img = Image("./pics/" + imgName)
                if not isinstance(img.img, type(None)):
                    self.imgs.append(img)
            except AttributeError:
                pass


    def downloadImgs(self, e):
        # TODO: switch to downloader module
        self.imgs = []
        self.tc2.SetValue("1")
        query = self.tc0.GetLineText(0) + " " + self.tc1.GetLineText(0)
        limit = str(10)
        output = "./pics"

        if query != "":
            os.system("del /q pics\\*")
            execute = "py bbid.py -s \"" + query + "\" --limit " + limit + " -o " + output
            os.system(execute)
            print("done downloading")
            self.processImgs()
        else:
            print("no query given")
        self.displayImg()

    def displayImg(self, e=None):
        select = int(self.tc2.GetLineText(0)) - 1
        if select not in range(len(self.imgs)):
            return

        # display contours to be drawn
        # TODO - fix color warning issue for some images 
        image = wx.Image(self.imgs[select].contImg.shape[1], self.imgs[select].contImg.shape[0])
        image.SetData(cv2.cvtColor(self.imgs[select].contImg, cv2.COLOR_BGR2RGB).tobytes())
        self.dispImg.SetBitmap(image.ConvertToBitmap())

        # set slider
        self.sld.SetValue(self.imgs[select].threshVal)
        self.panel.Refresh()

    def prevImg(self, e):
        val = int(self.tc2.GetLineText(0)) - 1
        if val not in range(1,len(self.imgs)):
            return
        self.tc2.SetValue(str(val))
        self.displayImg()

    def nextImg(self, e):
        val = int(self.tc2.GetLineText(0)) - 1
        if val not in range(len(self.imgs)-1):
            return
        self.tc2.SetValue(str(val+2))
        self.displayImg()

    def sliderChange(self, e):
        select = int(self.tc2.GetLineText(0)) - 1
        if select not in range(len(self.imgs)-1):
            return

        threshVal = e.GetEventObject().GetValue()
        self.imgs[select].setThresh(threshVal)

        self.displayImg()

    def startDraw(self, e):
        self.drawing = True;
        self.drawBut.SetLabel("Primed...") # Press alt at corner of drawing Area and release at opposite corner
        select = int(self.tc2.GetLineText(0)) - 1
        if select not in range(len(self.imgs)):
            return

        # make new thead daemon and start it
        draw_thread = threading.Thread(target=self.draw, args=(self.imgs[select],), daemon=True)

        draw_thread.start()

    def stopDraw(self):
        self.drawing = False;
        self.drawBut.SetLabel("Start Draw")

    def draw(self, img, fast=True):
        # TODO: consider refactoring this
        print("Awaiting start... (hold left alt and click-drag a box around the drawing area)")
        listener = Listener()
        areaStart, areaEnd, areaShape = (0,0), (0,0), (0,0)  

        key_down_flag = False
        while 1:
            if listener.key_pressed and listener.key == keyboard.Key.alt_l:
                # mark key down
                if not key_down_flag:
                    areaStart = pyautogui.position()
                key_down_flag = True
            else:
                # if key no longer down, execute
                if key_down_flag and not listener.mouse_left_down:
                    areaEnd = pyautogui.position()
                    break

            # cancel
            if(listener.key_pressed and (listener.key == keyboard.Key.esc or
                    listener.key == keyboard.Key.ctrl_l)):
                listener.stop()
                print("Drawing Cancelled!")
                time.sleep(0.5)
                return

            time.sleep(0.1)
        
        # account for different start/end points
        (areaStart, areaEnd) = ( ( min(areaStart[0], areaEnd[0]) , min(areaStart[1], areaEnd[1]) ),
                                 ( max(areaStart[0], areaEnd[0]), max(areaStart[1], areaEnd[1]) ) )
        areaShape = (areaEnd[1]-areaStart[1], areaEnd[0]-areaStart[0])

        # center drawing in draw area -- pyautogui does (x,y) vs numpy image (y,x)
        imgResize = img.getImg(areaShape)
        start_x = areaStart[0] + (areaShape[1] - imgResize.shape[1])/2 
        start_y = areaStart[1] + (areaShape[0] - imgResize.shape[0])/2 
        start = time.time()

        # draw longest contours first
        contours = sorted(img.getContours(areaShape), key = lambda x: cv2.arcLength(x, False), reverse = True)
        total = len(contours)

        cur = 0
        for c in contours:
            # if len(c) > 12 :
            if cv2.arcLength(c, False) > 10 and len(c) > 5:
                print(cur, "/", total, " length:", cv2.arcLength(c, False), end='\r')

                cur_x, cur_y = start_x + c[0][0][0], start_y + c[0][0][1]
                pyautogui.moveTo(cur_x, cur_y) 
                pyautogui.mouseDown()
                

                for i in range(1, len(c)):
                    x = start_x + c[i][0][0]
                    y = start_y + c[i][0][1]

                    if fast:
                        # skip points less than 5 away L1 norm on large contours
                        # TODO: adjust values or figure out moving with constant speed 
                        nextPointDist = abs(cur_x - x) + abs(cur_y - y)
                        if len(c) < 50 or nextPointDist > 5:
                            dur = 0.3 if nextPointDist > 50 else 0
                            pyautogui.moveTo(x,y,dur) 
                            cur_x = x
                            cur_y = y
                    else:
                        # pyautogui.moveTo(x,y, 0.01) 
                        pyautogui.moveTo(x,y, 0) 
                        cur_x = x
                        cur_y = y

                    # emergency stop
                    if(listener.key_pressed and (listener.key == keyboard.Key.esc or
                            listener.key == keyboard.Key.ctrl_l)):
                        pyautogui.mouseUp()
                        print("\nDrawing Cancelled!")
                        listener.stop()
                        self.stopDraw()
                        time.sleep(0.5)
                        return

                # close loop
                pyautogui.moveTo(start_x + c[0][0][0], start_y + c[0][0][1]) 
                pyautogui.mouseUp()

            cur += 1
        listener.stop()
        print()
        print("Time Elapsed:", time.time()-start)
        self.stopDraw()
        return

if __name__ == "__main__":
    app = wx.App()
    win = Skribblr(None, title='Skribblr!')
    win.Show()
    app.MainLoop()

    quit()
