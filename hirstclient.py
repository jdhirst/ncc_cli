#!/usr/bin/python
import owncloud
import sys
import os
import subprocess
import getpass
import ConfigParser
import base64
import time
import humanize
import multiprocessing
import owncloud as nclib
from tqdm import tqdm
from texttable import Texttable
from os.path import expanduser

class bcolors:
    BLUE = '\033[34m'
    DEFAULT = '\033[39m'
    YELLOW = '\033[93m'

home = expanduser("~")
if os.name == 'nt':
    configfile = home + "/hcfg.ini"
else:
    configfile = home + "/.hcfg"
Config = ConfigParser.ConfigParser()
Config.read(configfile)
cwd = os.getcwd()

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def connect():
    global session
    if not os.path.isfile(configfile):
        username_input = raw_input('Username: ')
        password_raw = getpass.getpass()
        password_encoded = base64.encodestring(password_raw)
        cfgfile = open(configfile,'w')
        Config.add_section('Config')
        Config.set('Config','username',username_input)
        Config.set('Config','password_base64',password_encoded)
        Config.write(cfgfile)
        cfgfile.close()
    cfguser = ConfigSectionMap("Config")['username']
    cfgpass_encoded = ConfigSectionMap("Config")['password_base64']
    cfgpass = base64.decodestring(cfgpass_encoded)
    session = nclib.Client('https://hirst.cloud/')
    session.login(cfguser,cfgpass)

def dl_getsize():
    global dl_rsize
    global dl_lsize
    fobj = session.file_info(dl_lpath)
    dl_rsize = fobj.get_size()

def dl_progress():
    pbar = tqdm(total=dl_rsize, unit_scale=True, unit="byte")
    dl_lsize = 1
    while dl_lsize < dl_rsize:
        if os.path.exists(dl_lpath):
            time.sleep(0.1)
            oldsize = dl_lsize
            dl_lsize = os.path.getsize(dl_lpath)
        else:
            oldsize = 0
            time.sleep(1.0)
        changesize = float(dl_lsize) - float(oldsize)
        pbar.update(changesize)
    pbar.close()

##### DEFINE USER COMMANDS BELOW #####

def ls(arg1,arg2=False):
    try:
        connect()
        output = session.list(arg1)
        t = Texttable()
        for i in output:
            if arg2 == True:
                if i.is_dir() == True:
                    t.add_row(["d",i.get_name(),"",i.get_content_type(),i.get_last_modified()])
                if i.is_dir() == False:
                    t.add_row(["",i.get_name(),humanize.naturalsize(i.get_size()),i.get_content_type(),i.get_last_modified()])
            elif arg2 == False:
                if i.is_dir() == True:
                    t.add_row(["d",bcolors.BLUE + i.get_name() + bcolors.DEFAULT,""])
                if i.is_dir() == False:
                    t.add_row(["",bcolors.DEFAULT + i.get_name() + bcolors.DEFAULT,humanize.naturalsize(i.get_size())])
        t.set_deco(t.VLINES)
        print t.draw()
    except:
        print "Error: could not list dir"

def put(arg1,arg2='/'):
    try:
        print "Uploading " + arg1
        connect()
        session.put_file(arg2,arg1)

        print "Upload Complete"

    except:
        print "Error: could not upload file"
    # TODO: progress indication

def putdir(arg1,arg2='/'):
    try:
        print "Uploading directory " + arg1
        connect()
        session.put_directory(arg2,arg1)
        print "Upload Complete"

    except:
        print "Error: could not upload directory"
    # TODO: progress indication

def getproc():
    try:
        print "Downloading " + getarg1
        session.get_file(getarg1,getarg2)
        time.sleep(1.0)
        print "Download Complete"
    except:
        print "Error: could not download file"


def get(arg1,arg2=None):
    global getarg1
    global getarg2
    getarg1 = arg1
    getarg2 = arg2
    connect()
    dl_getsize()
    copy = multiprocessing.Process(name='copy', target=getproc)
    prog = multiprocessing.Process(name='prog', target=dl_progress)
    copy.start()
    prog.start()

def getdir(arg1,arg2=None):
    try:
        print "Downloading zip of " + arg1
        connect()
        session.get_directory_as_zip(arg1,arg2)
        print "Download Complete"

    except:
        print "Error: could not download zip file"

    # TODO: progress indication

def mkdir(arg1):
    connect()
    try:
        result = session.mkdir(arg1)
        print "Created " + arg1
    except: 
        print "Error: could not create dir"

def rm(arg1):
    connect()
    try:
        print "WARNING: This command deletes files recursively."
        confirm = ""
        while confirm != "Y" and confirm != "N" and confirm != "y" and confirm != "n":
            confirm = raw_input('Are you sure you want to delete ' + arg1 + '? [Y/N]')
            print confirm
        if confirm == "Y" or confirm == "y":
            result = session.delete(arg1)
            print "Deleted " + arg1   
        elif confirm == "N" or confirm == "n":
            print "Operation Canceled"
            sys.exit(0)
    except: 
        print "Error: could not delete"

def share(arg1):
    #try:
    print "Creating public share"
    connect()
    share = session.share_file_with_link(arg1)
    print "\n=== Created Share Successfully ==="+ bcolors.YELLOW + "\n\nLink: " + share.get_link() + "\nShare Contents: " + share.get_path() + "\n" + bcolors.DEFAULT

    #except:
        #print "Error: could not create file share"
##### END COMMAND DEFINITIONS #####

def main():
    global dl_lpath
    global dl_rpath
    if len(sys.argv) == 1:
        print "No arguments provided."
        sys.exit(1)
    elif len(sys.argv) >= 2:
        if sys.argv[1] == "ls":
            if len(sys.argv) == 2:
                ls('/')
            else: 
                if len(sys.argv) == 3:
                    if sys.argv[2] == "-l":
                        ls('/',True)
                    else:
                        ls(sys.argv[2])
                else:
                    if sys.argv[2] == "-l":
                        ls(sys.argv[3],True)
                    else:
                        ls(sys.argv[2])

        elif sys.argv[1] == "mkdir":
            if len(sys.argv) == 2:
                print "Creates a new directory\nSyntax: mkdir <name>"
            else: 
                mkdir(sys.argv[2])

        elif sys.argv[1] == "rm":
            if len(sys.argv) == 2:
                print "Recursively deletes a file or directory\nSyntax: rm <name>"
            else: 
                rm(sys.argv[2])

        elif sys.argv[1] == "put":
            if len(sys.argv) == 2:
                print "Uploads a file\nSyntax: put [local source] <remote dest>"
            elif len(sys.argv) == 3:
                put(sys.argv[2])
            elif len(sys.argv) == 4:
                put(sys.argv[2],sys.argv[3])

        elif sys.argv[1] == "putdir":
            if len(sys.argv) == 2:
                print "Uploads a directory\nSyntax: putdir [local source] <remote dest>"
            elif len(sys.argv) == 3:
                putdir(sys.argv[2])
            elif len(sys.argv) == 4:
                putdir(sys.argv[2],sys.argv[3])

        elif sys.argv[1] == "get":
            if len(sys.argv) == 2:
                print "Downloads a file\nSyntax: get [remote source] <local dest>"
            elif len(sys.argv) == 3:
                dl_lpath = "./" + sys.argv[2].rsplit('/', 1)[-1]
                dl_rpath = sys.argv[2]
                get(sys.argv[2])
            elif len(sys.argv) == 4:
                dl_lpath = sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1]
                dl_rpath = sys.argv[2]
                get(sys.argv[2],sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1])
        elif sys.argv[1] == "getdir":
            if len(sys.argv) == 2:
                print "Downloads directory as zip archive\nSyntax: getdir [remote source] <local dest>"
            elif len(sys.argv) == 3:
                getdir(sys.argv[2],sys.argv[2].rsplit('/', 1)[-1] + '.zip')
            elif len(sys.argv) == 4:
                getdir(sys.argv[2],sys.argv[3])

        elif sys.argv[1] == "share":
            share(sys.argv[2])

        else:
            print "Invalid Command, please revise."
    else:
        print "Invalid Syntax, please revise."

if __name__ == '__main__':
    main()
