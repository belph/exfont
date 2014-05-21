import tkinter as tk
#import tkFileDialog as filedialog
#import tkMessageBox
from tkinter import filedialog, messagebox
import subprocess
import re
import sys
import configparser
from os import listdir, walk, path
from collections import namedtuple

# Various variables #########
 
tk.Tk()
subdir= tk.IntVar()
mkvd = tk.StringVar()
fdir = tk.StringVar()
inp = tk.StringVar() 

config = configparser.ConfigParser()

dataset = config.read('exfont.ini')
if len(dataset) != 1:
    config['DEFAULT']['mkv'] =  ""
    config['DEFAULT']['fontdir'] =  ""
    config['DEFAULT']['input'] = ""
    with open('exfont.ini','w') as configfile:
        config.write(configfile)
config.read('exfont.ini')

print_debug = False
flag = False
isDir = True
fontlist = []
filelist = []
fontdir = ""
video = ""

 
#if not video:
#    print("No video specified (parameter #1)")
#    input()
#    sys.exit(1)
 
match_extension = lambda name: re.search(r"\.(ttf|otf)$", name, re.I)
attachment_types = 'application/x-truetype-font'  # using `in` operator so this may be a tuple or list
 
mkvtoolnix = ""
regexp_track = re.compile(r"^Track ID (?P<id>\d+): (?P<type>\w+) \((?P<codec>[^\)]+)\)$", re.M)
regexp_attachment = re.compile(r"^Attachment ID (?P<id>\d+): type '(?P<type>[^']+)', size (?P<size>\d+) bytes, file name '(?P<name>[^']+)'$", re.M)
 
 
# Functions #################
 
def debug(*args):
    if print_debug:
        print(*args)

        
def getExistingFonts():
    global fontlist
    fontlist = listdir(fontdir)
    for i,font in enumerate(fontlist):
        isFont = match_extension(font)
        if not isFont:
            del fontlist[i]

def findMkv(folder="."):
    global filelist
    if flag:
        filelist = listdir(folder)
        for i,file in enumerate(filelist):
            if not file.endswith(".mkv"):
                del filelist[i]
    else:
        for root, dirs, files in walk(folder):
            for file in files:
                if file.endswith(".mkv"):
                    filelist.append(path.join(root,file))


def mkv(tool, *params):
    # cmd = '"%smkv%s.exe" %s' % (mkvtoolnix, tool, ' '.join(params) or '')
    cmd = ["%smkv%s.exe" % (mkvtoolnix, tool)] + list(params)
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e)
        print("Output:", e.output)
        sys.exit(2)
 
    return output.decode("cp1252").replace('\r', '').replace('\n\n', '\n')
 
# Use awesome namedtuples as a C "const struct"
MatroskaContainer = namedtuple("MatroskaContainer", 'tracks attachments')
Track = namedtuple("Track", 'id type codec')
Attachment = namedtuple("Attachment", 'id type size name')
 
 
def mkvidentify(video):
    identify = mkv("merge", "--identify", video)
    debug(identify)
 
    collect = lambda r, c: [c(*x) for x in r.findall(identify)]
 
    return MatroskaContainer(collect(regexp_track, Track),
                             collect(regexp_attachment, Attachment))
 
 
# The code ##################
 
def ex_main():
    # Collect information
    getExistingFonts()
    if isDir:
        findMkv(video)
    else: filelist.append(video)
    print("VIDEO FILES")
    for f in filelist:
        if ' ' in f: f = '"'+ f +'"'
        print(f)
        
    for vid in filelist:
        container = mkvidentify(vid)
        debug(container)
        attachments = container.attachments
        #print("Found %d attachments for %s" % (len(attachments), vid))
 
        count = 0
        for i, attach in enumerate(attachments):
            extension_matches = match_extension(attach.name)
            type_matches = attach.type in attachment_types
 
            # Disregard irrelevant attachments
            if attach.name in fontlist:
                print("Already have; Skipping '{0.name}'...({0.id})".format(attach))
                continue
            elif not extension_matches and not type_matches:
                print("Skipping '{0.name}'... ({0.id})".format(attach))
                continue
            elif not extension_matches:
                print("Type mismatch but extention of a font; still extracting... ('{0.name}', {0.type})".format(attach))
            elif not type_matches:
                print("Extension mismatch but type of a font; still extracting... ('{0.name}', {0.type})".format(attach))
            else:
                print("Extracting '{0.name}'...".format(attach))
 
            # Extract
            if '"' in fontdir:
                debug(mkv("extract", "attachments", vid, '{0.id}:{1}{0.name}"'.format(attach,fontdir[:-1])))
            else:
                debug(mkv("extract", "attachments", vid, '{0.id}:{1}{0.name}'.format(attach,fontdir)))
            count += 1
 
    # The end
    config['DEFAULT']['mkv'] =  mkvtoolnix
    config['DEFAULT']['fontdir'] =  fontdir
    config['DEFAULT']['input'] = video
    with open('exfont.ini','w') as configfile:
        config.write(configfile)
    messagebox.showinfo("Complete", "Extraction Complete.\nSuccessfully extracted %d fonts from %d files." % (count,len(filelist)))



def go():
    hasPassed = True
    print(mkvd.get(),fdir.get(),inp.get())
    global mkvtoolnix
    global fontdir
    global video
    global isDir
    if mkvd.get()=="":
        messagebox.showerror("Error", "You must specify the location of mkvtoolnix on your computer.")
        hasPassed = False
    if hasPassed==True and fdir.get()=="":
        messagebox.showerror("Error", "You must specify where you would like the fonts saved to.")
        hasPassed = False
    if hasPassed==True and inp.get()=="":
        messagebox.showerror("Error", "You must provide an input file or directory.")
        hasPassed = False
    
    if hasPassed:
        #Update Variables
        if subdir.get() == 0:
            flag=False
        mkvtoolnix = mkvd.get() +'/'
        fontdir = fdir.get() + '/'
        video = inp.get()
        if ' ' in mkvtoolnix: mkvtoolnix = '"'+ mkvtoolnix +'"'
        if ' ' in fontdir: fontdir = '"'+ fontdir +'"'
        #if ' ' in video: video = '"'+ video +'"'
        if video.endswith('.mkv"'):
            isDir = False
        if isDir: video = video + '/'
        ex_main()
    
    


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()

        
    def openDir(self, var):
        var.set(filedialog.askdirectory())

    def openFile(self, var):
        var.set(filedialog.askopenfilename(filetypes=[("MKV Files","*.mkv")]))
    
    def createWidgets(self):
        self.mkvDirLabel = tk.Label(self, text='mkvtoolnix Directory:')
        self.mkvDir = tk.Entry(self, textvariable=mkvd,width=60)
        self.mkvDirBut = tk.Button(self, text='Browse', command=lambda: self.openDir(mkvd))
        self.fontDirLabel = tk.Label(self, text='Font Directory:')
        self.fontDir = tk.Entry(self, textvariable=fdir,width=60)
        self.fontDirBut = tk.Button(self, text='Browse', command=lambda: self.openDir(fdir))
        self.inputLabel = tk.Label(self, text='Input File or Directory:')
        self.input = tk.Entry(self, textvariable=inp,width=60)
        self.inputDirBut = tk.Button(self, text='Browse Directories', command=lambda: self.openDir(inp))
        self.inputFileBut = tk.Button(self, text='Browse Files', command=lambda: self.openFile(inp))
        self.subdir = tk.Checkbutton(self,variable=subdir,text='Search Subdirectories')
        self.subdir.select()
        self.mkvDirLabel.grid(column=0,row=1,padx=5)
        self.mkvDir.grid(column=1,row=1)
        self.mkvDirBut.grid(column=2,row=1,pady=5)
        self.fontDirLabel.grid(column=0,row=2,padx=5)
        self.fontDir.grid(column=1,row=2)
        self.fontDirBut.grid(column=2,row=2,pady=5)
        self.inputLabel.grid(column=0,row=3,padx=5)
        self.input.grid(column=1,row=3)
        self.inputDirBut.grid(column=2,row=3,pady=5,padx=5)
        self.inputFileBut.grid(column=2,row=4,pady=5,padx=5)
        self.subdir.grid(column=1,row=4)
        self.quitButton = tk.Button(self, text='Quit',
            command=self.quit)
        self.quitButton.grid(column=1,row=5,pady=5)
        self.goButton = tk.Button(self, text='Extract',
            command=lambda: go())
        self.goButton.grid(column=0,row=5,pady=5)
        if config['DEFAULT']['mkv']: mkvd.set(config['DEFAULT']['mkv'])
        if config['DEFAULT']['fontdir']: fdir.set(config['DEFAULT']['fontdir'])
        if config['DEFAULT']['input']: inp.set(config['DEFAULT']['input'])
    
app = Application()
app.master.title('Font Extractor') 
app.mainloop()     
