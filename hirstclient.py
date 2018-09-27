#!/usr/bin/python
import owncloud
import sys
import os
import subprocess
import getpass
from os.path import expanduser
import ConfigParser
import base64
import owncloud as nclib

home = expanduser("~")
if os.name == 'nt':
    configfile = home + "/hcfg.ini"
else:
    configfile = home + "/.hcfg"
Config = ConfigParser.ConfigParser()
Config.read(configfile)
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



#print cfguser
#print cfgpass

def connect():
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
    session = nclib.Client('https://hirst.cloud')
    session.login(cfguser,cfgpass)
connect()
