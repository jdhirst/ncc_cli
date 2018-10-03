#!/usr/bin/python
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
from yaspin import yaspin
from yaspin.spinners import Spinners
from tqdm import tqdm
from texttable import Texttable
from os.path import expanduser

class bcolors:
    BLUE = '\033[34m'
    DEFAULT = '\033[39m'
    YELLOW = '\033[93m'

home = expanduser("~")
if os.name == 'nt':
    configfile = home + "/ncc_cfg.ini"
else:
    configfile = home + "/.ncc_cfg"
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
        print bcolors.YELLOW + "--- Initial Client Setup ---\n\nNOTE: Please enter full URI for server name.\nExample: https://myserver.com/nextcloud\nFor security reasons, please do not use your plaintext password for this utility. You should generate an App password from your NextCloud settings page.\n" + bcolors.DEFAULT
        servername_input = raw_input('Server URI: ')
        username_input = raw_input('Username: ')
        password_raw = getpass.getpass()
        password_encoded = base64.encodestring(password_raw)
        cfgfile = open(configfile,'w')
        Config.add_section('Config')
        Config.set('Config','servername',servername_input)
        Config.set('Config','username',username_input)
        Config.set('Config','password_base64',password_encoded)
        Config.write(cfgfile)
        cfgfile.close()
    cfguser = ConfigSectionMap("Config")['username']
    cfgpass_encoded = ConfigSectionMap("Config")['password_base64']
    servername = ConfigSectionMap("Config")['servername']
    cfgpass = base64.decodestring(cfgpass_encoded)
    session = nclib.Client(servername)
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

def zip_dl_progress():
    if os.path.exists(dl_lpath):
        print dl_lpath + " already exists"
    else:
        print "Downloading zip of " + getdirarg1
        dl_lsize = 1
        getdir_copy = multiprocessing.Process(name='getdir_copy', target=getdirproc)
        getdir_copy.start()
        pbar = tqdm(total=0, unit_scale=True, unit="byte")
        while getdir_copy.is_alive() == True:
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
        print "Download Complete"

##### DEFINE USER COMMANDS BELOW #####

def ls(arg1,arg2=False):
    debug = True
    if debug == True:
    #try:
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
    #except:
    #    print "Error: could not list dir"

def lsshare(arg1):
    try:
        connect()
        output = session.get_shares(path=arg1,subfiles=True)
        t = Texttable()
        t.header(["Path","Token","Date Created"])
        for i in output:
            t.add_row([i.get_path(),i.get_token(),i.get_share_time()])
        t.set_deco(t.VLINES | t.HEADER)
        print t.draw()
    except:
        print "Error: could not list shares"

def put(arg1,arg2='/'):
    try:
        print "Uploading " + arg1
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.put_file(arg2,arg1)
            time.sleep(1.0)
        print "Upload Complete"

    except:
        print "Error: could not upload file"
    # TODO: Better progress indication. Need library update for this.

def putdir(arg1,arg2='/'):
    try:
        print "Uploading directory " + arg1
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.put_directory(arg2,arg1)
            time.sleep(1.0)
        print "Upload Complete"

    except:
        print "Error: could not upload directory"
    # TODO: Better progress indication. Need library update for this.

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

def getdirproc():
    try:
        session.get_directory_as_zip(getdirarg1,getdirarg2)
    except:
        print "Error: could not download zip file"

def getdir(arg1,arg2=None):
    global getdirarg1
    global getdirarg2
    getdirarg1 = arg1
    getdirarg2 = arg2
    connect()
    getdir_prog = multiprocessing.Process(name='prog', target=zip_dl_progress)
    getdir_prog.start()

def mkdir(arg1):
    try:
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.mkdir(arg1)
            time.sleep(1.0)
        print "Created " + arg1
    except: 
        print "Error: could not create dir"

def copy(arg1,arg2):
    print "Copying " + arg1 + " to " + arg2
    with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
        sp.text = "Operation in Progress"
        connect()
        session.copy(arg1,arg2)
        time.sleep(1.0)
    print "Operation Completed"

def move(arg1,arg2):
    print "Moving " + arg1 + " to " + arg2
    with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
        sp.text = "Operation in Progress"
        connect()
        session.move(arg1,arg2)
        time.sleep(1.0)
    print "Operation Completed"

def rm(arg1):
    try:
        print "WARNING: This command deletes files recursively."
        confirm = ""
        while confirm != "Y" and confirm != "N" and confirm != "y" and confirm != "n":
            confirm = raw_input('Are you sure you want to delete ' + arg1 + '? [Y/N]')
        if confirm == "Y" or confirm == "y":
            with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
                sp.text = "Operation in Progress"
                connect()
                session.delete(arg1)
                time.sleep(1.0)
            print "Deleted " + arg1   
        elif confirm == "N" or confirm == "n":
            print "Operation Canceled"
            sys.exit(0)
    except: 
        print "Error: could not delete"

def mkshare(arg1):
    try:
        print "Creating public share"
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            share = session.share_file_with_link(arg1)
            time.sleep(1.0)
        print "\n=== Created Share Successfully ==="+ bcolors.YELLOW + "\n\nLink: " + share.get_link() + "\nShare Contents: " + share.get_path() + "\n" + bcolors.DEFAULT

    except:
        print "Error: could not create file share"

def rmshare(arg1):
    try:
        print "Loading Share: " + arg1
        confirm = ""
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            output = session.get_shares(arg1)
            sharepath = ""
            for i in output:
                sharepath = i.get_path()
        if sharepath == "":
            print "Share not found"
        else:
            while confirm != "Y" and confirm != "N" and confirm != "y" and confirm != "n":
                confirm = raw_input('Are you sure you want to delete share ' + sharepath + '? [Y/N]')
            if confirm == "Y" or confirm == "y":
                print "Deleting public share"
                with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
                    for i in output:
                        sp.text = "Operation in Progress"
                        session.delete_share(i.get_id())
                        time.sleep(1.0)
            print "\nOperation Completed"

    except:
        print "Error: could not delete file share"
##### END COMMAND DEFINITIONS #####

def main():
    global dl_lpath
    global dl_rpath
    if (len(sys.argv) == 1) or (sys.argv[1] == "-h") or (sys.argv[1] == "--help"):
        t = Texttable()
        t.set_deco(t.VLINES)
        print "No arguments provided."
        print "\nSyntax: " + sys.argv[0] + " [command] <arguments>\n"
        t.add_row(["ls","(-l) <dir>","lists dir contents"])
        t.add_row(["put","[local file] <dest remote dir>","uploads file"])
        t.add_row(["putdir","[local dir] <dest remote dir>","uploads dir"])
        t.add_row(["get","[remote file] <dest local dir>","downloads file"])
        t.add_row(["getdir","[remote dir] <dest local dir>","downloads dir as zip"])
        t.add_row(["mkdir","[dir name]","creates new dir"])
        t.add_row(["rm","[dir/file name]","deletes files or dirs"])
        t.add_row(["mkshare","[dir/file name]","creates new share w/link"])
        t.add_row(["lsshare","[dir name]","lists shares in dir"])
        t.add_row(["rmshare","[dir/file name]","deletes share"])
        t.add_row(["cp","[source] [destination]","copies files on server"])
        t.add_row(["mv","[source] [destination]","moves files on server"])
        print t.draw()
        sys.exit()
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
        elif sys.argv[1] == "lsshare":
            if len(sys.argv) == 2:
                lsshare('/')
            else: 
                if len(sys.argv) == 3:
                    lsshare(sys.argv[2])
                else:
                    lsshare(sys.argv[2])

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
                dl_lpath = "./" + sys.argv[2].rsplit('/', 1)[-1] + '.zip'
                dl_rpath = sys.argv[2]
                getdir(sys.argv[2],sys.argv[2].rsplit('/', 1)[-1] + '.zip')
            elif len(sys.argv) == 4:
                dl_lpath = sys.argv[3]
                dl_rpath = sys.argv[2]
                getdir(sys.argv[2],sys.argv[3])
        elif sys.argv[1] == "cp":
            if (len(sys.argv) == 2) or (len(sys.argv) == 3):
                print "Copies file within cloud\nSyntax: cp [source file] [destination dir]"
            elif len(sys.argv) == 4:
                copy(sys.argv[2],sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1])
        elif sys.argv[1] == "mv":
            if (len(sys.argv) == 2) or (len(sys.argv) == 3):
                print "Moves file within cloud\nSyntax: mv [source file] [destination dir]"
            elif len(sys.argv) == 4:
                move(sys.argv[2],sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1])
        elif sys.argv[1] == "mkshare":
            if len(sys.argv) == 2:
                print "Creates new share with link from supplied file/directory\nSyntax: mkshare [remote file/dirname]"
            else: 
                mkshare(sys.argv[2])
        elif sys.argv[1] == "rmshare":
            if len(sys.argv) == 2:
                print "Deletes file share from supplied file/directory\nSyntax: rmshare [remote file/dirname]"
            else: 
                rmshare(sys.argv[2])
        else:
            print "Invalid Command, please revise."
    else:
        print "Invalid Syntax, please revise."

if __name__ == '__main__':
    try: 
        main()
    except KeyboardInterrupt:
        print "Operation Interrupted"
        sys.exit()
