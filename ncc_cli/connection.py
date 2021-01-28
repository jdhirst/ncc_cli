#This file deals with connections to the NextCloud server
import os,configparser,sys,getpass,base64,traceback
import owncloud as nclib
from ncc_cli.utils import *

def ConfigSectionMap(Config, section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                debugPrint("skip: %s" % option)
        except Exception as e:
            print("exception on %s!" % option + "\n" + str(e))
            dict1[option] = None
    return dict1

def generateConfig(Config, configfile):
    print(bcolours.YELLOW + "--- Initial Client Setup ---\n\nNOTE: Please enter full URI for server name.\nExample: https://myserver.com/nextcloud\nFor security reasons, please do not use your plaintext password for this utility. You should generate an App password from your NextCloud settings page.\n" + bcolours.DEFAULT)
    servername_input = input('Server URI: ')
    username_input = input('Username: ')
    password_raw = getpass.getpass()
    password_bytes = password_raw.encode("utf-8") #Unused?
    password_encoded = base64.b64encode(password_raw.encode("utf-8"))
    cfgfile = open(configfile,'w')
    Config.add_section('Config')
    Config.set('Config','servername',servername_input)
    Config.set('Config','username',username_input)
    Config.set('Config','password_base64',password_encoded.decode("utf-8"))
    Config.write(cfgfile)
    cfgfile.close()

def initializeConfig():
    home = os.path.expanduser("~")
    if os.name == 'nt': #If on Windows, use ini extension
        configfile = home + "/ncc_cfg.ini"
    else: #Elsewhere, use UNIX hidden filename
        configfile = home + "/.ncc_cfg"

    #Initialize config object
    Config = configparser.ConfigParser()

    #Check if config file exists or not
    if not os.path.isfile(configfile):
        generateConfig(Config, configfile)

    #Read contents of configfile into Config object
    Config.read(configfile)

    #Finally, return config object
    return Config

def connect():
    Config = initializeConfig()
    cfguser = ConfigSectionMap(Config, "Config")['username']
    cfgpass_encoded = ConfigSectionMap(Config, "Config")['password_base64']
    servername = ConfigSectionMap(Config, "Config")['servername']
    cfgpass = base64.b64decode(cfgpass_encoded)
    try:
        session = nclib.Client(servername)
        session.login(cfguser,cfgpass)
        return session
    except Exception as e:
        print("\nERROR: Unable to connect to the server. Please check provided URL.\n")
        print("\n ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())