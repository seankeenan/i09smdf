#
# some c/ping from wxpython-demo, as in OnNickMenu
#


#Python modules
import os
import threading
import socket
import identd
import time

#UI modules
import wx

#Python-IRC modules
import extras

ID_ABOUT = wx.NewId()
ID_EXIT = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_SAVEAS = wx.NewId()

# function event drudge

EVT_PRINT_MESSAGE = wx.PyEventBinder(wx.NewEventType(), 1)
ID_PRINT_MESSAGE = wx.NewId()
EVT_SEND_MESSAGE = wx.PyEventBinder(wx.NewEventType(), 1)
ID_SEND_MESSAGE = wx.NewId()
EVT_NEW_NICKS = wx.PyEventBinder(wx.NewEventType(), 1)
ID_NEW_NICKS = wx.NewId()
EVT_REMOVE_NICK = wx.PyEventBinder(wx.NewEventType(), 1)
ID_REMOVE_NICK = wx.NewId()
EVT_JOIN_ROOM = wx.PyEventBinder(wx.NewEventType(), 1)
ID_JOIN_ROOM = wx.NewId()

#development defaults
#defaultroom = '#sean'
defaultserver = "irc.afternet.org"
#defaultuser = 'rollybot'
defaultroom = '#sean'
#defaultserver = "niven.freenode.net"
defaultuser = 'sean7'
botmode = True
import pdb

################################################################################
# via http://weblog.patrice.ch/2009/01/05/proper-file-overwrites-in-python.html
# doesn't work yet...
#import portalocker
#if os.name == 'posix':
#    # Rely on the atomicity of Posix renames.
#    rename = os.rename
#else:
#    def _rename(src, dst):
#        """Rename the file or directory src to dst. If dst exists and is a
#        file, it will be replaced silently if the user has permission.
#        """
#        if os.path.exists(src) and os.path.isfile(dst):
#            os.remove(dst)
#        os.rename(src, dst)
#
#def write2(filename, contents):
#    filename_tmp = filename + '.TMP'
#    with open(filename_tmp, 'a') as lockfile:
#        portalocker.lock(lockfile, portalocker.LOCK_EX)
#        with open(filename_tmp, 'w') as out_file:
#            out_file.write(contents)
#    rename(filename_tmp, filename)
# back to our regularly scheduled programming
################################################################################

class Sock(threading.Thread):
    def __init__(self, servername, username):
        threading.Thread.__init__(self)
        self.servername = servername
        self.username = username
        self.realname = username
        self.handler = wx.EvtHandler()
        self.handler.Bind(EVT_SEND_MESSAGE, self.sendMessage)
        self.handler.Bind(EVT_JOIN_ROOM, self.joinRoom)
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
        self.s.sendall("NICK %s\r\n" % self.username)
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
                    #self.s.sendall("JOIN %s \r\n" % defaultroom)
                    continue
                printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
                printevent.SetString(msg)
                wx.PostEvent(frame, printevent)
                #frame.GetEventHandler().ProcessEvent(event)
                #if ("NOTICE AUTH :***" in line):
                
    def safesend(self, cmd, msg):
        if len(msg) + len(cmd) < 500:
            self.s.sendall(cmd + msg + "\r\n")
        else:
            print "Your message is too long: %s ..." % msg[:25]

    def recvrn(self):
        self.buf += self.s.recv(512)
        while self.buf.find("\r\n") != -1:
            msg, self.buf = self.buf.split("\r\n", 1)
            yield msg

    def joinRoom(self, e):
        self.s.sendall("JOIN %s \r\n" % e.GetString())

    def sendMessage(self, e):
        room = e.GetClientData()
        msg = e.GetString()
        self.s.sendall("PRIVMSG %s :%s\r\n" % (room, msg))
    
    def botParse(self, nick, room, msg):
        #botcommands = {'roll':}
        if ' ' in msg:
            cmd, msg = msg.split(' ',1)
            if cmd.lower() == 'roll':
                result, valid = extras.roll(msg)
                report = "%s is rolling %s: %s" % (nick, msg, result)
                if len(report) > 480:
                    report = "Seriously, %s? You crazy." % nick
                printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
                printevent.SetString(report)
                printevent.SetClientData(room)
                event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
                event.SetString(report)
                event.SetClientData(room)
                wx.PostEvent(frame.sock.handler, event)
                wx.PostEvent(frame, printevent)
                #frame.sock.handler.ProcessEvent(event)
                #frame.GetEventHandler().ProcessEvent(printevent)
                return

    def parseMessage(self, msg):
        printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        user = None
        debugmsg = msg
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
            if room == self.username: # whisper
                room = nick
                event = wx.PyCommandEvent(EVT_JOIN_ROOM.typeId, ID_JOIN_ROOM)
                event.SetString(room)
                wx.PostEvent(frame, event)
                #frame.GetEventHandler().ProcessEvent(event)
            if botmode:
                self.botParse(nick, room, msg[1:])
            printevent.SetString("<" + nick + "> " + msg[1:])
            printevent.SetClientData(room)
            wx.PostEvent(frame, printevent)
            #frame.GetEventHandler().ProcessEvent(printevent)
        elif cmd == "353": # RPL_NAMREPLY
            selfnick, equalsign, room, users = msg.split(" ",3)
            users = users[1:].split(" ")
            nickevent = wx.PyCommandEvent(EVT_NEW_NICKS.typeId, ID_NEW_NICKS)
            nickevent.SetClientData(users)
            wx.PostEvent(frame.rooms[room.lower()].nicks, nickevent)
            #frame.rooms[room.lower()].nicks.ProcessEvent(nickevent)
        elif cmd == "JOIN":
            nickevent = wx.PyCommandEvent(EVT_NEW_NICKS.typeId, ID_NEW_NICKS)
            nickevent.SetClientData([nick])
            if ':' in msg:
                msg = msg.replace(':','')
                event = wx.PyCommandEvent(EVT_JOIN_ROOM.typeId, ID_JOIN_ROOM)
                event.SetString(msg)
                #frame.sock.handler.ProcessEvent(event)
                wx.PostEvent(frame, event)
                #frame.GetEventHandler().ProcessEvent(event)
            else:
                frame.rooms[msg.lower()].nicks.ProcessEvent(nickevent)
                printevent.SetString(nick + " has joined %s" % msg)
                printevent.SetClientData(msg)
                wx.PostEvent(frame, printevent)
                #frame.GetEventHandler().ProcessEvent(printevent)
        elif cmd == "QUIT":
            printevent.SetString(nick + " quit: (%s)" % msg[1:])
            print nick, user, host, cmd, msg
            printevent.SetClientData(defaultroom) # quit messages don't have a room...
            wx.PostEvent(frame, printevent)
            #frame.GetEventHandler().ProcessEvent(printevent)
            nickevent = wx.PyCommandEvent(EVT_REMOVE_NICK.typeId, ID_REMOVE_NICK)
            nickevent.SetClientData(nick)
            wx.PostEvent(frame.rooms[defaultroom].nicks, nickevent)
            #frame.rooms[defaultroom].nicks.ProcessEvent(nickevent)
        elif cmd == "366": # End of /NAMES list
            return
        else:
            printevent.SetString(nick + " " + cmd + " " + msg)
            wx.PostEvent(frame, printevent)
            #frame.GetEventHandler().ProcessEvent(printevent)
    
class ChatWindow(wx.Panel):
    def __init__(self, parent, id, title):
        global frame
        wx.Panel.__init__(self, parent, id, name = title, size = (800, 400))#, pos = (200, 100))

        self.room = wx.TextCtrl(self, 1, style=(wx.TE_MULTILINE
                                                | wx.TE_AUTO_URL
                                                | wx.TE_READONLY
                                                | wx.VSCROLL
                                                | wx.ALWAYS_SHOW_SB
                                                | wx.TE_RICH))
        #self.room.SetEditable(False)

        self.nicklist = []
        self.nicks = wx.ListBox(self, wx.ID_ANY, style=(wx.LB_SORT | wx.LB_NEEDED_SB | wx.LB_SINGLE))
        self.nicks.Bind(wx.EVT_RIGHT_UP, self.OnNickMenu)
        self.nicks.Bind(EVT_NEW_NICKS, self.OnNewNicks)
        self.nicks.Bind(EVT_REMOVE_NICK, self.OnRemoveNick)

        self.buffer = wx.TextCtrl(self, 2, style=wx.TE_PROCESS_ENTER)
        self.buffer.Bind(wx.EVT_TEXT_ENTER, self.process_message , self.buffer) 

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
        
        self.roomtitle = title
        
        self.buffer.Bind(wx.EVT_CHAR, self.OnChar)
        self.nicks.Bind(wx.EVT_CHAR, self.OnChar)
        self.room.Bind(wx.EVT_CHAR, self.OnChar)

    def OnChar(self, e):
        #print e.GetKeyCode(), e.ControlDown()
        e.Skip()

    def private_message(self, msg): # not even used...
        # doing it wrong - should be able to event.settype
        event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
        event.SetString(e.GetString())
        event.SetClientData(self.roomtitle)
        frame.sock.handler.ProcessEvent(event)
        printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        printevent.SetString(e.GetString())
        printevent.SetClientData(self.roomtitle)
        wx.PostEvent(frame, printevent)
        #frame.GetEventHandler().ProcessEvent(printevent)
        e.GetClientObject().Clear()

    def process_message(self, e):
        msg = e.GetString()
        if msg[:6].lower() == "/join ": # better way to do this? probably. I'll refactor later. FLW.
            event = wx.PyCommandEvent(EVT_JOIN_ROOM.typeId, ID_JOIN_ROOM)
            event.SetString(msg[6:])
            wx.PostEvent(frame.sock.handler, event)
            #frame.sock.handler.ProcessEvent(event)
            wx.PostEvent(frame, event)
            #frame.GetEventHandler().ProcessEvent(event)
            # feels wrong, but e.Skip and e.ResumePropagation
            # aren't working as I would expect
            # TRY: trawl wxpy-demo?
            printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
            printevent.SetString("Joining " + msg[6:])
            printevent.SetClientData(self.roomtitle)
            wx.PostEvent(frame, printevent)
            #frame.GetEventHandler().ProcessEvent(printevent)
            e.GetClientObject().Clear()
            return
        elif msg[:6].lower() == "/roll ":
            msg = msg[6:]
            result, valid = extras.roll(msg)
            report = "rolling %s: %s" % (msg, result)
            printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
            printevent.SetString(report)
            printevent.SetClientData(self.roomtitle)
            event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
            event.SetString(report)
            event.SetClientData(self.roomtitle)
            wx.PostEvent(frame.sock.handler, event)
            wx.PostEvent(frame, printevent)
            #frame.sock.handler.ProcessEvent(event)
            #frame.GetEventHandler().ProcessEvent(printevent)
            e.GetClientObject().Clear()
            return
        elif msg:
            event = wx.PyCommandEvent(EVT_SEND_MESSAGE.typeId, ID_SEND_MESSAGE)
            event.SetString(msg)
            event.SetClientData(self.roomtitle)
            wx.PostEvent(frame.sock.handler, event)
            #frame.sock.handler.ProcessEvent(event)
            printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
            printevent.SetString("me: " + msg)
            printevent.SetClientData(self.roomtitle)
            wx.PostEvent(frame, printevent)
            #frame.GetEventHandler().ProcessEvent(printevent)
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
        # send message should incorporate self.nick
        ## should add self.nick
        event.SetString(msg)
        event.SetClientData(self.roomtitle)
        printevent = wx.PyCommandEvent(EVT_PRINT_MESSAGE.typeId, ID_PRINT_MESSAGE)
        printevent.SetString(msg)
        printevent.SetClientData(self.roomtitle)
        wx.PostEvent(frame, printevent)
        wx.PostEvent(frame.sock.handler, event)
        #frame.GetEventHandler().ProcessEvent(printevent)
        #frame.sock.handler.ProcessEvent(event)

class TestNB(wx.Notebook):
    def __init__(self, parent, id):
        wx.Notebook.__init__(self, parent, id, #size=(21,21),
                             style= wx.BK_DEFAULT #| wx.WANTS_CHARS
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnKeyDown(self, e):
        #print e.GetKeyCode()
        #print "OnChar!"
        e.Skip()

class MainWindow(wx.Frame):
    def __init__(self,parent,id,title):
        #self.Bind(EVT_PRINT_MESSAGE, self.OnMessageToPrint)
        
        self.dirname = '' # pseudo unused
        self.server = defaultserver 
        self.username = defaultuser
        
        
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size = (500, 400), pos = (0, 100))#wx.ID_ANY, title, size = (200,100))
        
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        
        # Setting up the #presently unused# menu.
        filemenu= wx.Menu()
        filemenu.Append(ID_OPEN, "&Open", "Open a file.")
        filemenu.Append(ID_SAVE, "&Save", "Save the file.")
        filemenu.Append(ID_SAVEAS, "Sa&ve as", "Save the file.")
        filemenu.AppendSeparator()
        filemenu.Append(ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT,"E&xit"," Terminate the program")
        #wx.EVT_TEXT_ENTER(self, ID_OPEN, self.OnOpen)
        
        ## CLEAN: sloppy, sloppy, copy pasted...
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        EVT_PRINT_MESSAGE(self, ID_PRINT_MESSAGE, self.OnMessageToPrint)
        self.Bind(EVT_JOIN_ROOM, self.joinRoom)
        
        self.sock = Sock(self.server, self.username)
        self.sock.start()
        
        self.tabs = TestNB(self, wx.ID_ANY)
        self.tabcount = -1

        self.rooms = {}
        self.tabs.Bind(wx.EVT_CHAR, self.OnChar)
        
        event = wx.PyCommandEvent(EVT_JOIN_ROOM.typeId, ID_JOIN_ROOM)
        event.SetString(self.server)
        #wx.PostEvent(self.sock.handler, event)
        wx.PostEvent(self, event)
        #self.sock.handler.ProcessEvent(event)
        #self.GetEventHandler().ProcessEvent(event)

        #self.rooms[defaultroom] = ChatWindow(self.tabs, wx.ID_ANY, defaultroom)
        #self.rooms[defaultroom].Show()
        #self.tabs.AddPage(self.rooms[defaultroom], defaultroom)
        #self.tabs.Show()
        self.Show()
        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the  MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        #self.Show(True)
    
    def OnChar(self, e):
        print e.GetKeyCode()
    
    def joinRoom(self,e):
        # todo - support Caps in channel names :/ see onMessageToPrint
        room = e.GetString()
        if room.lower() not in self.rooms:
            self.tabcount += 1
            self.rooms[room.lower()] = ChatWindow(self.tabs, wx.ID_ANY, room)
            self.tabs.AddPage(self.rooms[room.lower()], room.lower())
            self.tabs.ChangeSelection(self.tabcount)
            self.rooms[room.lower()].buffer.SetFocus()

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
            # very possibly an exception at present
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
        # very possibly an exception at present
        f.close()

    def OnMessageToPrint(self,e):
        #todo - caps in room names - see joinRoom
        msg = e.GetString()
        room = e.GetClientData()
        if room:
            if len(msg):
                if room.lower() not in self.rooms:
                    #event = wx.PyCommandEvent(EVT_JOIN_ROOM.typeId, ID_JOIN_ROOM)
                    #event.SetString(room)
                    #self.GetEventHandler().ProcessEvent(event)
                    print room, msg, "Do I get here? FIX!"
                else:
                    self.rooms[room.lower()].room.write("\n" + msg) #err.. rooms room room write? telephone fail :(
                    self.rooms[room.lower()].room.ScrollLines(1)
        else:
            self.rooms[self.server].room.write("\n" + msg)
            self.rooms[self.server].room.ScrollLines(1)

app = wx.PySimpleApp()
frame = MainWindow(None, -1, "Simple client")
app.MainLoop()