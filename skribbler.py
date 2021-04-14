import pyautogui 
import keyboard
import time
import cv2
import numpy as np
import sys
import os
import wx

pyautogui.MINIMUM_DURATION = 0.01 # default: 0.1
pyautogui.MINIMUM_SLEEP = 0.02 # default: 0.05
pyautogui.PAUSE = 0.01 # default: 0.1

def process_img(img_path):
    im = cv2.imread(img_path)

    factor_x = 650. / im.shape[0] 
    factor_y = 900. / im.shape[1] 
    factor = min(factor_x, factor_y)
    print("factor:", factor)
    new_dim = (int(im.shape[1] * factor), int(im.shape[0] * factor)) 

    im = cv2.resize(im, new_dim)

    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(imgray,200,255,0)
    conts, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    # black_cnt = np.zeros((512,512,3), np.uint8)
    # img = cv2.drawContours(black_cnt, conts, -1, (0,255,0), 3)

    return im, thresh, conts 

def show_img(thresh):
    cv2.imshow("thresh", thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def show_cont(conts, img):
    black_cnt = np.zeros((img.shape[0],img.shape[1],3), np.uint8)
    img = cv2.drawContours(black_cnt, conts, -1, (0,255,0), 3)

    cv2.imshow("contour", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def show_thresh(thresh):
    cv2.imshow("thresh", thresh)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def draw(conts, start_x, start_y, fast=True):
    print(start_x, start_y)

    conts.sort(key = len, reverse = True)
    total = len(conts)

    cur = 0
    for c in conts:
        print(cur, "/", total, " size:",len(c))
        if(len(c) > 8):
            pyautogui.moveTo(start_x + c[0][0][0],
                    start_y + c[0][0][1]) 

            cur_x = start_x + c[0][0][0]
            cur_y = start_y + c[0][0][1]

            pyautogui.mouseDown()
            for i in range(1, len(c)):
                x = start_x + c[i][0][0]
                y = start_y + c[i][0][1]
                # print(abs(cur_x - x) + abs(cur_y - y))

                if fast != True:
                    # pyautogui.moveTo(x,y)
                    pyautogui.moveTo(x,y, duration = 0.01) 
                    cur_x = x
                    cur_y = y
                else:
                    if(abs((cur_x - x)) + abs(cur_y - y) > 5):
                        if(abs((cur_x - x)) + abs(cur_y - y) > 20):
                            pyautogui.moveTo(x,y, duration = 0.1) 
                        else:
                            pyautogui.moveTo(x,y) 

                        cur_x = x
                        cur_y = y

                if(keyboard.is_pressed('q')):
                    # emergency exit
                    pyautogui.mouseUp()
                    time.sleep(0.5)
                    return

            # always complete loop
            pyautogui.moveTo(start_x + c[0][0][0], start_y + c[0][0][1]) 
            pyautogui.mouseUp()
            cur += 1
        else:
            return



def total_size(contours):
    total = 0
    for i in contours:
        total += len(i)
    return total

def download_images(keyword, limit, output):
    os.system("del /q pics\*")
    # os.system("ls")
    execute = "py bbid.py -s \"" + keyword + "\" --limit " + limit + " -o " + output
    os.system(execute)
    os.system("del /q pics\*.gif")

if __name__ == "__main__":

    # initialize
    img_path = ""
    global img, thresh, conts

    app = wx.App()
    app.MainLoop()

    while(1):

        if(keyboard.is_pressed('a')):
            print("processing...")
            img, thresh, conts = process_img("./fuck_off.jpg")
            time.sleep(.5)
            print("Done")
            msg = wx.MessageDialog(None, "Done!")
            msg.ShowModal()
            msg.Destroy()

        if(keyboard.is_pressed('d')):
            # dlg = wx.TextEntryDialog(None, "Image search for: ")
            dlg = wx.TextEntryDialog(None, "Image search for: ",
                    style = wx.OK | wx.CANCEL | wx.STAY_ON_TOP,
                    pos = wx.Point(500, 500))
            dlg.ShowModal()

            keyword = dlg.GetValue()
            limit = str(10)
            output = "./pics"

            dlg.Destroy()
            if(keyword != ""):
                download_images(keyword, limit, output)
                print("done downloading")
            else:
                print("no keyword given")

            select_msg = "\n".join(os.listdir("./pics"))

            dlg = wx.TextEntryDialog(None, select_msg,
                    style = wx.OK | wx.CANCEL | wx.STAY_ON_TOP,
                    pos = wx.Point(500, 500))
            dlg.ShowModal()

            select = int(dlg.GetValue())

            keyword = dlg.GetValue()
            img_path = os.listdir("./pics")[select - 1]
            img, thresh, conts = process_img("./pics/" + img_path)
            time.sleep(.5)
            msg = wx.GenericMessageDialog(None, "Processed!", style = wx.STAY_ON_TOP) 
            msg.ShowModal()
            msg.Destroy()


        # if(keyboard.is_pressed('l')):
        #     print(os.listdir("./pics"))
        #     img_path = os.listdir("./pics")[0]
        #     msg = wx.GenericMessageDialog(None, "Selected!", style = wx.STAY_ON_TOP) 
        #     msg.ShowModal()
        #     msg.Destroy()
        #     time.sleep(.5)

        if(keyboard.is_pressed('p')):
            print("processing...")
            dlg = wx.TextEntryDialog(None, "Select Image: ",
                    style = wx.OK | wx.CANCEL | wx.STAY_ON_TOP,
                    pos = wx.Point(500, 500))
            dlg.ShowModal()

            select = int(dlg.GetValue())

            keyword = dlg.GetValue()
            img_path = os.listdir("./pics")[select - 1]
            img, thresh, conts = process_img("./pics/" + img_path)
            time.sleep(.5)
            msg = wx.GenericMessageDialog(None, "Processed!", style = wx.STAY_ON_TOP) 
            msg.ShowModal()
            msg.Destroy()

        if(keyboard.is_pressed('w')):
            cur_x, cur_y = pyautogui.position()
            start = time.time()
            draw(conts, cur_x, cur_y, False)
            print("Time Elapsed:", time.time()-start)

        if(keyboard.is_pressed('s')):
            cur_x, cur_y = pyautogui.position()
            start = time.time()
            # draw(conts, cur_x, cur_y, False)
            draw(conts, cur_x, cur_y, True)
            print("Time Elapsed:", time.time()-start)

        if(keyboard.is_pressed('o')):
            print(pyautogui.position())
            time.sleep(.5)

        if(keyboard.is_pressed('i')):
            cv2.imshow("image", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if(keyboard.is_pressed('c')):
            show_cont(conts, img)

        if(keyboard.is_pressed('t')):
            show_thresh(thresh)

        if(keyboard.is_pressed('q')):
            break
