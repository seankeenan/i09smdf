import wx
import os
import portalocker
import threading
import socket
import identd
ID_ABOUT = wx.NewId()
ID_EXIT = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_SAVEAS = wx.NewId()
ID_PRINT_MESSAGE = wx.NewId()
ID_SEND_MESSAGE = wx.NewId()
ID_NEW_NICKS = wx.NewId()
ID_REMOVE_NICK = wx.NewId()
EVT_PRINT_MESSAGE = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_SEND_MESSAGE = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_NEW_NICKS = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_REMOVE_NICK = wx.PyEventBinder(wx.NewEventType(), 1)

if os.name == 'posix':
    # Rely on the atomicity of Posix renames.
    rename = os.rename
else:
    def _rename(src, dst):
        """Rename the file or directory src to dst. If dst exists and is a
        file, it will be replaced silently if the user has permission.
        """
        if os.path.exists(src) and os.path.isfile(dst):
            os.remove(dst)
        os.rename(src, dst)

def write2(filename, contents):
    filename_tmp = filename + '.TMP'
    with open(filename_tmp, 'a') as lockfile:
        portalocker.lock(lockfile, portalocker.LOCK_EX)
        with open(filename_tmp, 'w') as out_file:
            out_file.write(contents)
    rename(filename_tmp, filename)

class Sock(threading.Thread):
    def __init__(self, servername, username):
        threading.Thread.__init__(self)
        self.servername = servername
        self.username = username
        self.realname = username
        self.handler = wx.EvtHandler()
        self.handler.Bind(EVT_SEND_MESSAGE, self.sendMessage)
        self.buf = ""

    def run(self):
        #create an INET, STREAMing socket
        ident = identd.Identd(self.username)
        ident.start()
        global frame
        self.s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        #s.connect(("www.google.com", 80))
        self.s.connect((self.servername, 6667))
        msg = True
        #f = open("test.txt", "w")
        #i = 0
        #s.sendall("USER guessed tolmoon tolsun :Nicholas")
        self.s.sendall("NICK seank7\r\n")
        #USER <username> <hostname> <servername> :<realname>
        self.s.sendall("USER %s %s %s :%s\r\n" % (self.username, self.username, self.username, self.realname ))
        
        while 1:
            for msg in self.recvrn():
                if msg[:1] == ":":
                   self.parseMessage(msg)
                   continue
    
                    #f.write(line)
                    #print line
                if msg[:4] == "PING":
                    self.s.sendall("PONG " + msg[5:] + "\r\n")
                    self.s.sendall("JOIN #ShantyTown \r\n")
                    continue
                event = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
                event.SetClientData(msg)
                frame.GetEventHandler().ProcessEvent(event)
                #if ("NOTICE AUTH :***" in line):
                #    

    def recvrn(self):
        self.buf += self.s.recv(512)
        while self.buf.find("\r\n") != -1:
            msg, self.buf = self.buf.split("\r\n", 1)
            yield msg

    def sendMessage(self, e):
        self.s.sendall("PRIVMSG #ShantyTown :%s\r\n" % e.GetClientData())
        
    def parseMessage(self, msg):
        printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        user = None
        if msg.find(" ") == -1:
            print "debug? : " + msg
            return
        
        user, msg = msg[1:].split(" ", 1)
        nick = user
        if "!" in user:
            nick, user = user.split("!")
            user, host = user.split("@")
        cmd, msg = msg.split(" ", 1)
        if cmd == "PRIVMSG":
            room, msg = msg.split(" ", 1)
            printevent.SetClientData("<" + nick + "> " + msg[1:])
            frame.GetEventHandler().ProcessEvent(printevent)
        elif cmd == "353":
            selfnick, equalsign, channel, users = msg.split(" ",3)
            users = users[1:].split(" ")
            nickevent = wx.PyCommandEvent(EVT_NEW_NICKS.typeId, ID_NEW_NICKS)
            nickevent.SetClientData(users)
            frame.a.nicks.ProcessEvent(nickevent)
        elif cmd == "JOIN":
            nickevent = wx.PyCommandEvent(EVT_NEW_NICKS.typeId, ID_NEW_NICKS)
            nickevent.SetClientData([nick])
            frame.a.nicks.ProcessEvent(nickevent)
            printevent.SetClientData(nick + " has joined %s" % msg)
            frame.GetEventHandler().ProcessEvent(printevent)
        elif cmd == "QUIT":
            printevent.SetClientData(nick + "quit: (%s)" % msg[1:])
            nickevent = wx.PyCommandEvent(EVT_REMOVE_NICK.typeId, ID_REMOVE_NICK)
            nickevent.SetClientData(nick)
            frame.a.nicks.ProcessEvent(nickevent)
        else:
            printevent.SetClientData(nick + " " + cmd + " " + msg)
            frame.GetEventHandler().ProcessEvent(printevent)
            
    
    
class ChatWindow(wx.Frame):
    def __init__(self, parent, id, title):
        global frame
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size = (800, 400), pos = (200, 100))#wx.ID_ANY, title, size = (200,100))
        self.room = wx.TextCtrl(self, 1, style=(wx.TE_MULTILINE | wx.TE_AUTO_URL))
        self.room.SetEditable(False)
        self.nicks = wx.ListBox(self, wx.ID_ANY, style=(wx.LB_SORT | wx.LB_NEEDED_SB | wx.LB_SINGLE))
        self.nicklist = []
        self.nicks.Bind(wx.EVT_RIGHT_UP, self.OnNickMenu)
        self.nicks.Bind(EVT_NEW_NICKS, self.OnNewNicks)
        self.nicks.Bind(EVT_REMOVE_NICK, self.OnRemoveNick)
        
        self.buffer = wx.TextCtrl(self, 2, style=wx.TE_PROCESS_ENTER)
        self.buffer.Bind(wx.EVT_TEXT_ENTER, self.process_message , self.buffer) 
        
        #self.SplitHorizontally(self.room, self.buffer, 90)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2.Add(self.room, 9, wx.EXPAND)
        self.sizer2.Add(self.nicks, 0, wx.EXPAND)    
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.sizer2, 9, wx.EXPAND)
        self.sizer.Add(self.buffer, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.SetMinSize((1000, 500))
        self.SetAutoLayout(True)
        self.sizer.Fit(self)        
        self.Show(True)

    def private_message(self, msg):
        event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
        event.SetClientData(e.GetString())
        frame.sock.handler.ProcessEvent(event)
        event = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        event.SetClientData(e.GetString())
        frame.GetEventHandler().ProcessEvent(event)
        e.GetClientObject().Clear()

    def process_message(self, e):
        event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
        event.SetClientData(e.GetString())
        frame.sock.handler.ProcessEvent(event)
        event = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        event.SetClientData("me: " + e.GetString())
        frame.GetEventHandler().ProcessEvent(event)
        e.GetClientObject().Clear()

    def OnNewNicks(self, e):
        for user in e.GetClientData():
            if user not in self.nicklist:
                self.nicklist.append(user)
                self.nicks.Append(user,0)
    
    def OnRemoveNick(self, e):
        user = e.GetClientData()
        if user in self.nicklist:
            n = self.nicks.FindString(user)
            if n != wx.NOT_FOUND:
                self.nicks.Delete(n)
                self.nicklist.remove(user)
        
    def OnNickMenu(self, e):
        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 
        if not hasattr(self, "popupId1"):
            self.popupId1 = wx.NewId()
            self.troutId = wx.NewId()
            
            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupId1)
            self.Bind(wx.EVT_MENU, self.OnTrout, id=self.troutId)

        item = self.nicks.HitTest(e.GetPosition())
        self.nicks.SetSelection(item)
        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupId1, "One")
        menu.Append(self.troutId, "Trout")
        
        ## make a submenu
        #sm = wx.Menu()
        #sm.Append(self.popupID8, "sub item 1")
        #sm.Append(self.popupID9, "sub item 1")
        #menu.AppendMenu(self.popupID7, "Test Submenu", sm)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def OnPopupOne(self, e):
        print "popup one"
        
    def OnTrout(self, e):
        msg = "I am testing a menu item on %s" % self.nicks.GetStringSelection()
        event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
        event.SetClientData(msg)
        event = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        event.SetClientData(msg)
        frame.GetEventHandler().ProcessEvent(event)
        frame.sock.handler.ProcessEvent(event)

class MainWindow(wx.Frame):
    def __init__(self,parent,id,title):
        
        #self.Bind(EVT_PRINT_MESSAGE, self.OnMessageToPrint)
        
        self.dirname = ''
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size = (500, 400), pos = (0, 100))#wx.ID_ANY, title, size = (200,100))
        self.a = ChatWindow(self, wx.ID_ANY, 'name')
        
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        
        # Setting up the menu.
        filemenu= wx.Menu()
        filemenu.Append(ID_OPEN, "&Open", "Open a file.")
        filemenu.Append(ID_SAVE, "&Save", "Save the file.")
        filemenu.Append(ID_SAVEAS, "Sa&ve as", "Save the file.")
        filemenu.AppendSeparator()
        filemenu.Append(ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT,"E&xit"," Terminate the program")
        #wx.EVT_TEXT_ENTER(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        
        EVT_PRINT_MESSAGE(self, ID_PRINT_MESSAGE, self.OnMessageToPrint)
        self.sock = Sock("irc.afternet.org", "sean9002902")
        self.sock.start()
        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        #self.Show(True)

    def OnAbout(self,e):
        d= wx.MessageDialog( self, " A sample editor \n"
                           " in wxPython","About Sample Editor", wx.OK)
                           # Create a message dialog box
        d.ShowModal() # Shows it
        d.Destroy() # finally destroy it when finished.
    def OnExit(self,e):
        self.Close(True)  # Close the frame.
        
    def OnOpen(self,e):
        """ Open a file"""
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename=dlg.GetFilename()
            self.dirname=dlg.GetDirectory()
            f=open(os.path.join(self.dirname,self.filename),'r')
            self.control['main'].SetValue(f.read())
            f.close()
        dlg.Destroy()
    
    def OnSaveAs(self,e):
        """ Save file as... dialog. Same precautions as OnSave should be followed"""
        if not self.dirname:
            self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.SAVE) #| wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename=dlg.GetFilename()
            self.dirname=dlg.GetDirectory()
            dst = os.path.join(self.dirname,self.filename)
            f = open(dst, "w")
            f.write(self.control['main'].Value)
            f.close()
        dlg.Destroy()
        
    def OnSave(self,e):
        """ Save a file
        It is important to note that this is not really a safe method.
        That shouldn't often matter, but it's important to note.
        For whatever reason, the portalocker method gets permission denied and
        I don't want to deal with it now.   """
        if not self.dirname:
            self.OnSaveAs(e)
        dst = os.path.join(self.dirname,self.filename)
        f = open(dst, "w")
        f.write(self.control['main'].Value)
        f.close()
        
    def OnMessageToPrint(self,e):
        msg = e.GetClientData()
        if len(msg):
            self.a.room.write("\n" + msg)
        
            #msg = s.recv(512)   
            #msg = msg.split("\r\n")
            #for line in msg:
            #    f.write(line)
            #    print line
            #    if line[:4] == "PING":
            #        print "sent PONG" + line[5:]
            #        s.sendall("PONG " + line[5:] + "\r\n")
            ##if ("NOTICE AUTH :***" in line):
            #

app = wx.PySimpleApp()
frame = MainWindow(None, -1, "Simple client")


app.MainLoop()