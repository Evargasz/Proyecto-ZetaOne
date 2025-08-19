import tkinter as tk
from ..styles import FUENTE_GENERAL

class ToolTip:
    def __init__(self, widget, gettext):
        self.widget = widget
        self.gettext = gettext
        self.tipwindow = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)
        self.lastrow = None
    def enter(self, event=None):
        self.showtip(event)
    def motion(self, event):
        iid = self.widget.identify_row(event.y)
        if iid != self.lastrow:
            self.hidetip()
            self.lastrow = iid
            self.showtip(event)
    def leave(self, event=None):
        self.hidetip()
    def showtip(self, event):
        try:
            x, y, _, _ = self.widget.bbox("active")
        except Exception:
            x, y = 0, 0
        absx = self.widget.winfo_rootx() + 80
        absy = self.widget.winfo_rooty() + y + 30
        iid = self.widget.identify_row(event.y)
        texto = self.gettext(iid) if iid else ""
        if texto and iid:
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(1)
            tw.wm_geometry("+%d+%d" % (absx, absy))
            label = tk.Label(tw, text=texto, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             font=FUENTE_GENERAL)
            label.pack(ipadx=1)
    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None