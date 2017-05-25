#!/usr/bin/env python3

import os
import os.path
import sys
import subprocess
import requests
import signal
from bs4 import BeautifulSoup, SoupStrainer

# global constants
REMOTE_URL='git://git.kali.org/packages/{PACKAGE}.git'
PACKAGE_FOLDER='dist/'


# ##################################################################
#                              DATA
# ##################################################################

import data

# ##################################################################
#                       HELPER FUNCTIONS
# ##################################################################

# Helper that handles Ctrl-D
def readInput(str):
    print(str)
    line = sys.stdin.readline()
    if line:
        line = line.replace("\r", "").replace("\n", "")
        return line
    else: # user pressed C-D, i.e. stdin has been
        print("Quitting.")
        sys.exit(1)

#register the Ctrl-C and others to have a clean exit
def handleInterrupts():
    def signal_handler(signal, frame):
        print("Quitting.")
        sys.exit(1)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGFPE, signal_handler)
    signal.signal(signal.SIGILL, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# checks if a program is installed system-wide by running it in a subprocess and checking for error
def isInstalled(program):
    try:
        # pipe output to /dev/null for silence
        null = open("/dev/null", "w")
        subprocess.Popen(program, stdout=null, stderr=null)
        null.close()
        return True

    except OSError:
        return False

# if git is not installed, exit 1
def isGitInstalled():
    if not isInstalled("git"):
        print("git is required for this script to work. Please install it manually, e.g.:")
        print("   $ sudo apt-get install git")
        print("        or")
        print("   $ sudo dnf install git")
        print(" etc.")
        print("Exiting, status 1.")
        sys.exit(1)

# calls git clone, and wait for exit
def gitClone(repo, localDir):
    try:
        # pipe output to /dev/null for silence
        null = open("/dev/null", "w")
        subprocess.call(["git", "clone", repo, localDir])
        null.close()

    except OSError:
        print("Could not clone...")
        print("Exiting, status 1.")
        sys.exit(1)

# main function that checks if we need to clone a package, if so, run the post-install scripts
def installIfNeeded(package):
    dirName = PACKAGE_FOLDER+package

    if isInstalled(package):
        print(package, "seems already installed. Skipping")
        return

    print("Testing if", package, "exists locally...")
    if not os.path.isdir(dirName) :
        url = REMOTE_URL.replace("{PACKAGE}", package)
        print("Not found, gonna clone in", dirName)
        gitClone(url, dirName)

        if package in data.postInstall:
            print("Found post-install script(s)")
            for s in data.postInstall[package]:
                os.system("cd " + dirName + " && " + s)

# main function that tries to run a program (possibly cloning it before)
def run(package):

    #if package is already installed on the system via package manager, just call it
    if isInstalled(package):
        print(package, "seems already installed system-wide, calling it")
        os.system(package)

    #or, maybe clone the git, and run it
    else:
        installIfNeeded(package)

        # if we know how to run it, call the command
        if package in data.runCmds:
            print("Running", package)
            os.system(data.runCmds[package])

        #if we don't, try to guess
        else:
            baseName = PACKAGE_FOLDER+package+"/"+package

            if os.path.isfile(baseName+".sh"):
                print("Found an executable:", baseName+".sh", "running it... (Ctrl-C to exit)")
                os.system(baseName+".sh")
            elif os.path.isfile(baseName+".py"):
                print("Found an executable:", baseName+".py", "running it... (Ctrl-C to exit)")
                os.system(baseName+".py")
            elif os.path.isfile(baseName+".pl"):
                print("Found an executable:", baseName+".pl", "running it... (Ctrl-C to exit)")
                os.system(baseName+".pl")
            #finally, we give up
            else:
                print("Please run the program in", PACKAGE_FOLDER, package)

# test all packages names against the reference URL, shows broken links / packages
def testAllURLs():
    allPackages = []
    for cat in data.packages:
        allPackages += data.packages[cat]
    allPackages = set(allPackages)
    allPackages = sorted(list(allPackages))

    #get the page referencing all packages
    source = ""
    try:
        print("Contacting web server...")
        req = requests.get("http://git.kali.org/gitweb/", timeout=30)
        print("Done.")
        source = req.text
    except:
        print("Could not read git repos")
        sys.exit(1)

    #for each package, check if in page
    for p in allPackages:
        if p not in data.specialGitURL:
            fullPath = "packages/"+p+".git"
            if p not in source:
                print("Error", p, "@", fullPath, "not found.")


# ##################################################################
#                         MAIN LOGIC
# ##################################################################

def printHeader():
    print (''' _  _    __    __    ____     ____  _____  _____  __    ___ 
( )/ )  /__\  (  )  (_  _)___(_  _)(  _  )(  _  )(  )  / __)
 )  (  /(__)\  )(__  _)(_(___) )(   )(_)(  )(_)(  )(__ \__ 
(_)\_)(__)(__)(____)(____)    (__) (_____)(_____)(____)(___/''')

def printKaliMenu():
    print('''
Please select a category:

1) Information Gathering            8) Exploitation Tools
2) Vulnerability Analysis           9) Forensics Tools
3) Wireless Attacks                 10) Stress Testing
4) Web Applications                 11) Password Attacks
5) Sniffing & Spoofing              12) Reverse Engineering
6) Maintaining Access               13) Hardware Hacking
7) Reporting Tools                  14) Extra
''')
    action = ""
    while not action.isdigit() or int(action)<1 or int(action)>14 or not str(action) in data.packages:
        action = readInput("Category: ")
    printKaliSubMenu(str(action))

# prints one of Kali's categories
def printKaliSubMenu(id):
    ps = data.packages[id]

    #compute a map to find the package given the number
    m = {}

    longestStr = len(max(ps, key=len))
    print("")
    i = 1
    for p in ps:
        m[i] = p
        spaces = ' ' * (longestStr - len(p))
        description = ""
        if p in data.desc:
            description = data.desc[p]
        if i < 10 :
            print(' '+ str(i) + ") "+p, spaces, description)
        else:
            print(str(i) + ") "+p, spaces, description)
        i += 1
    print("")
    no = ""
    while not no.isdigit() or int(no)<1 or int(no)>=i:
        no = readInput("Package No: ")

    selectedPackage = m[int(no)]
    printSelectedPackage(selectedPackage)

# prints the selected package, test if installed, and asks wheter to run it
def printSelectedPackage(p):
    print("")
    print("Package\033[1m", p, "\033[0m") #just to put in bold

    dirName = PACKAGE_FOLDER+p
    if isInstalled(p) or os.path.isdir(dirName):
        print("This package is already installed.")
    else:
        print("This package is\033[1m not\033[0m installed, and will be downloaded if you try to run it.")

    ans = ""
    while ans != "y" and ans != "n" :
        ans = readInput('Would you like to run it ? [Y/n] ').lower()

    if ans == "y":
        print("")
        run(p)
    else:
        printKaliMenu()

# entry point
handleInterrupts()
isGitInstalled()
#printHeader()
#printKaliMenu()
# use this to test if all packages are still hosted correctly
# testAllURLs()

# fetches the links to get the full description of the pacakge
def fetchPackageLinks():
    d = requests.get("http://tools.kali.org/tools-listing")
    rawHtml = d.text
    soup = BeautifulSoup(rawHtml, 'html.parser')
    links = {}
    for link in soup.find_all('a'):
        if "<a href=\"http://tools.kali.org/" in str(link) :
            package = link.string.lower().replace(" ", "-")
            links[package] = link.get('href')

    #for l in sorted(links.keys()):
    #    print("links['"+l+"'] = \""+links[l]+"\"")

    return links

def fetchPackageDescription(links):
    for p in sorted(data.desc.keys()):
        if data.desc[p] == "":
            if p in links:
                #print("Getting doc for", p)
                d = requests.get(links[p])

                out = ""
                if d.status_code == 200 :
                    rawHtml = d.text
                    soup = BeautifulSoup(rawHtml, 'html.parser')
                    for s in soup.find_all('section'):
                        if "Package Description" in str(s):
                            for par in s.find_all('p'):
                                if not "Homepage" in par.text:
                                    t = par.text.strip()
                                    if not t.endswith("."):
                                        t += "."
                                    out += t + " "
                    print("desc['"+p+"'] = \""+out.replace("\"", "\\\"")+"\"")

l = fetchPackageLinks()
fetchPackageDescription(l)