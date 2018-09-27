#!/usr/bin/python
import owncloud
import sys
import os
import subprocess
import getpass
import ConfigParser
import base64
import owncloud as nclib
from os.path import expanduser

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

##### DEFINE COMMANDS BELOW #####

def ls(arg1):
    try:
        connect()
        output = session.list(arg1)
        print output
    except:
        print "Error: could not list dir"
    # TODO: parse file output in a pretty way

def put(arg1,arg2):
    try:
        print "Uploading " + arg1 + " to " + arg2
        connect()
        session.put_file(arg2,arg1)
        print "Upload Complete"

    except:
        print "Error: could not upload file"
    # TODO: progress indication

def get(arg1,arg2):
    try:
        print "Downloading " + arg1 + " to " + arg2
        connect()
        session.get_file(arg2,arg1)
        print "Download Complete"

    except:
        print "Error: could not download file"
    # TODO: progress indication

def putdir(arg1,arg2):
    try:
        print "Uploading directory " + arg1 + " to " + arg2
        connect()
        session.put_directory(arg2,arg1)
        print "Upload Complete"

    except:
        print "Error: could not upload directory"
    # TODO: progress indication

def getdir(arg1,arg2):
    try:
        print "Downloading zip of " + arg1 + " to " + arg2
        connect()
        session.get_directory_as_zip(arg2,arg1)
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
        while (confirm != "Y") or (conf != "N"):
            username_input = raw_input('Are you sure you want to delete ' + arg1 + '? [Y/N]')
        if confirm == "Y":
            result = session.mkdir(arg1)
            print "Deleted " + arg1   
        elif confirm == "N":
            print "Operation Canceled"
    except: 
        print "Error: could not create dir"

##### END COMMAND DEFINITIONS #####

def main():
    if len(sys.argv) == 1:
        print "No arguments provided."
        sys.exit(1)
    elif len(sys.argv) >= 2:
        if sys.argv[1] == "ls":
            if len(sys.argv) == 2:
                ls('/')
            else: 
                ls(sys.argv[2])
        elif sys.argv[1] == "mkdir":
            if len(sys.argv) == 2:
                print "Syntax: mkdir <name>"
            else: 
                mkdir(sys.argv[2])
        elif sys.argv[1] == "rm":
            if len(sys.argv) == 2:
                print "Syntax: rm <name>"
            else: 
                mkdir(sys.argv[2])
        elif sys.argv[1] == "put":
            if len(sys.argv) == 2:
                print "Syntax: put [source] <dest>"
            elif len(sys.argv) == 3:
                put('/',sys.argv[2])
            elif len[sys.argv] == 4:
                put(sys.argv[2],sys.argv[3])
        elif sys.argv[1] == "putdir":
            if len(sys.argv) == 2:
                print "Syntax: putdir [source] <dest>"
            elif len(sys.argv) == 3:
                putdir('/',sys.argv[2])
            elif len[sys.argv] == 4:
                putdir(sys.argv[2],sys.argv[3])
        elif sys.argv[1] == "get":
            if len(sys.argv) == 2:
                print "Syntax: get [source] <dest>"
            elif len(sys.argv) == 3:
                get(sys.argv[2],cwd)
            elif len[sys.argv] == 4:
                get(sys.argv[2],sys.argv[3])
        elif sys.argv[1] == "getdir":
            if len(sys.argv) == 2:
                print "Syntax: getdir [source] <dest>"
            elif len(sys.argv) == 3:
                getdir(sys.argv[2],cwd)
            elif len[sys.argv] == 4:
                getdir(sys.argv[2],sys.argv[3])
    else:
        print "Invalid Syntax, please revise."

if __name__ == '__main__':
    main()
