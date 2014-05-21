# ======FONT EXTRACTOR v1.0======
# -------------belph-------------
#
# Major credit given to FitcheFoll, whose mkv extracting script
# (https://gist.github.com/FichteFoll/4488489) I have modified
# to create this.

# This script extracts all font attachments of a Matroska file
# or directory tree containing multiple files. It also checks
# the output font directory to avoid duplicates.

# If something breaks, let me know on Github or (if it's an
# emergency) at #irrational-typesetting-wizardry on Rizon
# (my handle is sud0).

# Feature requests are welcome; acceptance is not guaranteed.

# -belph/sud0


# Requirements:	 mkvtoolnix
#				 (if running as a .py): Python 3.x

# INSTALLATION ######
# ============
#
# .PY FILE
# Save this file somewhere convenient to access from the command
# line. MODIFY THE FONTDIR AND MKVTOOLNIX VARIABLES AS DESIRED (important). You're good.
# See Usage.
#
# .EXE FILE (COMMAND LINE)
# Download zip file, save somewhere, and MODIFY FONTDIR AND MKVTOOLNIX IN INI FILE.
# See Usage.
#
# .EXE FILE (GUI)
# Download and use. Seriously, why are you reading this?
#

# USAGE ######
# =====
# .py file: exfont.py [mkv file or directory] [option]
# .exe file (command line): exfont [mkv file or directory] [option]
# (If no directory is entered, program will default to searching its own directory)
# 
# There is one option: -s will stop the program from searching subfolders
# of the given directory for mkv files.
 
import subprocess
import re
import sys
from os import listdir, walk, path
from collections import namedtuple
 
# Various variables #########
 
print_debug = False
flag = False
isDir = True
fontlist = []
filelist = []
fontdir = "C:\\Users\\Philip\\Documents\\MoonToons\\Fonts2\\"
try:
	video = sys.argv[1]
	givenArg = True
except:
	video = ""
	givenArg = False

try:
	if sys.argv[2] == '-s':
		flag = True
except:
	pass
if video == '-s':
	flag = True


if video.endswith(".mkv"):
	isDir = False
 
#if not video:
#    print("No video specified (parameter #1)")
#    input()
#    sys.exit(1)
 
match_extension = lambda name: re.search(r"\.(ttf|otf)$", name, re.I)
attachment_types = 'application/x-truetype-font'  # using `in` operator so this may be a tuple or list
 
mkvtoolnix = "C:\\Users\\Philip\\Downloads\\mkvtoolnix-6.8.0\\mkvtoolnix\\"
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
 
def main():
    # Collect information
    getExistingFonts()
    if isDir:
        if (video == '-s') or (givenArg==False):
            findMkv()
        else:
            findMkv(video)
    else: filelist.append(video)
    print("VIDEO FILES")
    for f in filelist:
        print(f)
    for vid in filelist:
        container = mkvidentify(vid)
        debug(container)
        attachments = container.attachments
        print("Found %d attachments for %s" % (len(attachments), vid))
 
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
            debug(mkv("extract", "attachments", vid, '{0.id}:{1}{0.name}'.format(attach,fontdir)))
            count += 1
 
    # The end
    print("Extracted %d fonts." % count)
    
 
if __name__ == "__main__":
    main()
