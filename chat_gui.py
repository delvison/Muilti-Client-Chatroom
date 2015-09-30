from tkinter import *
import chat_client as client
from chat_client import *

class chat_gui(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid()
        self.master.title("Grid Manager")

        for r in range(6):
            self.master.rowconfigure(r, weight=1)
        for c in range(5):
            self.master.columnconfigure(c, weight=1)
            Button(master, text="Button {0}".format(c)).grid(row=6,column=c,sticky=E+W)

        self.Frame1 = Frame(master, bg="red")
        self.Frame1.grid(row = 0, column = 0, rowspan = 3, columnspan = 1, sticky = W+E+N+S)
        self.Frame2 = Frame(master, bg="blue")
        self.Frame2.grid(row = 3, column = 0, rowspan = 3, columnspan = 1, sticky = W+E+N+S)
        self.Frame3 = Frame(master, bg="green")
        self.Frame3.grid(row = 0, column = 1, rowspan = 5, columnspan = 3, sticky = W+E+N+S)
        self.Frame4 = Frame(master, bg="yellow")
        self.Frame4.grid(row = 5, column = 1, rowspan = 1, columnspan = 3, sticky = W+E+N+S)

        self.initialize()
        self.after(1000,print("hi"))

    def initialize(self):
        # set up chat list
        self.gui_userlist = Listbox(self.Frame1)
        self.gui_userlist.pack(side="left",expand=1,fill="both")
        self.userlist_scrollbar = Scrollbar(self.Frame1,orient="vertical")
        self.userlist_scrollbar.config(command=self.gui_userlist.yview)
        self.userlist_scrollbar.pack(side="left",fill="both")
        self.gui_userlist.config(yscrollcommand=self.userlist_scrollbar.set)

        # set up connection part
        self.s_label=Label(self.Frame2, text="Server_IP")
        self.p_label=Label(self.Frame2, text="Server_Port")
        self.u_label=Label(self.Frame2, text="Username")
        self.server = Entry(self.Frame2)
        self.port = Entry(self.Frame2)
        self.user = Entry(self.Frame2)
        self.connect = Button(self.Frame2,text="Connect",command=self.connect)
        self.s_label.grid(row=0,column=0)
        self.p_label.grid(row=1,column=0)
        self.u_label.grid(row=2,column=0)
        self.server.grid(row=0,column=1,columnspan=3)
        self.port.grid(row=1,column=1,columnspan=3)
        self.user.grid(row=2,column=1,columnspan=3)
        self.connect.grid(row=3,column=1)

        # set up chat pane
        self.chat = Text(self.Frame3)
        self.chat.pack(side="left",expand=1,fill="both")
        self.chat_scrollbar = Scrollbar(self.Frame3,orient="vertical")
        self.chat_scrollbar.config(command=self.chat.yview)
        self.chat_scrollbar.pack(side="left",fill="both")
        self.chat.config(yscrollcommand=self.chat_scrollbar.set)

        # set up message input
        self.msg = Entry(self.Frame4)
        self.msg.bind("<Return>", self.send_msg)
        self.msg.pack(side="left",expand=1,fill="both")

    def connect(self):
        print(self.server.get())

    def send_msg(self, event):
        print(self.msg.get())
        self.msg.delete(0,END)


# root = Tk()
# app = chat_gui(master=root)
# app.mainloop()
