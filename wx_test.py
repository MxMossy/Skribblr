import wx

def ask(parent=None, message='', default_value=''):
    dlg = wx.TextEntryDialog(parent, message, value=default_value,
            style = wx.OK | wx.CANCEL | wx.STAY_ON_TOP)
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    return result

# Initialize wx App
app = wx.App()
app.MainLoop()

# Call Dialog
x = ask(message = 'What is your name?')
print('Your name was', x)
