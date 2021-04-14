import wx

class SelectableFrame(wx.Frame):

    c1 = None
    c2 = None

    def __init__(self, parent=None, id=-1, title=""):
        wx.Frame.__init__(self, parent, id, title, size=wx.DisplaySize())

        self.panel = wx.Panel(self, size=self.GetSize())

        self.panel.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.panel.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)

        self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        self.SetTransparent(50)

    def OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.c2 = event.GetPosition()
            self.Refresh()

    def OnMouseDown(self, event):
        self.c1 = event.GetPosition()

    def OnMouseUp(self, event):
        self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def OnPaint(self, event):
        if self.c1 is None or self.c2 is None: return

        dc = wx.PaintDC(self.panel)
        dc.SetPen(wx.Pen('red', 1))
        dc.SetBrush(wx.Brush(wx.Color(0, 0, 0), wx.TRANSPARENT))

        dc.DrawRectangle(self.c1.x, self.c1.y, self.c2.x - self.c1.x, self.c2.y - self.c1.y)

    def PrintPosition(self, pos):
        return str(pos.x) + " " + str(pos.y)


class MyApp(wx.App):

    def OnInit(self):
        frame = SelectableFrame()
        frame.Show(True)
        self.SetTopWindow(frame)

        return True


app = MyApp(0)
app.MainLoop()
