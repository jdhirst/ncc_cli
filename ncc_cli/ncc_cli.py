#!/usr/bin/python3
import sys,os,subprocess,getpass,configparser,base64,time,humanize,multiprocessing,argparse,traceback
import owncloud as nclib
from yaspin import yaspin
from yaspin.spinners import Spinners
from tqdm import tqdm
from texttable import Texttable

version = "0.0.7" #Define current version

class bcolours: #Define some pretty colours to be used later
    BLUE = '\033[34m'
    DEFAULT = '\033[39m'
    YELLOW = '\033[93m'

home = os.path.expanduser("~")
if os.name == 'nt': #If on Windows, use ini extension
    configfile = home + "/ncc_cfg.ini"
else: #Elsewhere, use UNIX hidden filename
    configfile = home + "/.ncc_cfg"
Config = configparser.ConfigParser()
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
        except Exception as e:
            print("exception on %s!" % option + "\n" + str(e))
            dict1[option] = None
    return dict1

def connect():
    global session
    if not os.path.isfile(configfile):
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
    cfguser = ConfigSectionMap("Config")['username']
    cfgpass_encoded = ConfigSectionMap("Config")['password_base64']
    servername = ConfigSectionMap("Config")['servername']
    cfgpass = base64.b64decode(cfgpass_encoded)
    try:
        session = nclib.Client(servername)
        session.login(cfguser,cfgpass)
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def dl_getsize():
    global dl_rsize
    global dl_lsize
    fobj = session.file_info(dl_rpath)
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
        print(dl_lpath + " already exists")
    else:
        try:
            print("Downloading zip of " + getdirarg1)
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
            print("Download Complete")
        except Exception as e:
            print("ERR: " + str(e) + "\n\nStack Trace:\n")
            print(traceback.format_exc())

##### DEFINE USER COMMANDS BELOW #####

def ls(lsDir,longOutput=False):
    try:
        connect()
        output = session.list(lsDir)
        t = Texttable()
        for i in output:
            if longOutput == True:
                if i.is_dir() == True:
                    t.add_row(["d",i.get_name(),"",i.get_content_type(),i.get_last_modified()])
                if i.is_dir() == False:
                    t.add_row(["",i.get_name(),humanize.naturalsize(i.get_size()),i.get_content_type(),i.get_last_modified()])
            elif longOutput == False:
                if i.is_dir() == True:
                    t.add_row(["d",bcolours.BLUE + i.get_name() + bcolours.DEFAULT,""])
                if i.is_dir() == False:
                    t.add_row(["",bcolours.DEFAULT + i.get_name() + bcolours.DEFAULT,humanize.naturalsize(i.get_size())])
        t.set_deco(t.VLINES)
        print(t.draw())
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def lsshare(lsDir):
    try:
        connect()
        output = session.get_shares(path=lsDir,subfiles=True)
        t = Texttable()
        t.header(["Path","Token","Date Created"])
        for i in output:
            t.add_row([i.get_path(),i.get_token(),i.get_share_time()])
        t.set_deco(t.VLINES | t.HEADER)
        print(t.draw())
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def put(arg1,arg2='/'):
    try:
        print("Uploading " + arg1)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.put_file(arg2,arg1)
        print("Upload Complete")

    except Exception as e:
        print("Error: could not upload file:\n" + str(e))
    # TODO: Better progress indication. Need library update for this.

def putdir(arg1,arg2='/'):
    try:
        print("Uploading directory " + arg1)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.put_directory(arg2,arg1)
        print("Upload Complete")

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())
    # TODO: Better progress indication. Need library update for this.

def getproc():
    try:
        print("Downloading " + getarg1)
        session.get_file(getarg1,getarg2)
        print("Download Complete")
    except Exception as e:
        print("Error: could not download file:\n" + str(e))

def get(arg1,arg2=None):
    try:
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
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def getdirproc():
    try:
        session.get_directory_as_zip(getdirarg1,getdirarg2)
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def getdir(arg1,arg2=None):
    try:
        global getdirarg1
        global getdirarg2
        getdirarg1 = arg1
        getdirarg2 = arg2
        connect()
        getdir_prog = multiprocessing.Process(name='prog', target=zip_dl_progress)
        getdir_prog.start()
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def mkdir(mkDir):
    try:
        connect()
        session.mkdir(mkDir)
        print("created " + mkDir)
    except Exception as e: 
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def copy(arg1,arg2):
    try:
        print ("Copying " + arg1 + " to " + arg2)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.copy(arg1,arg2)
        print("Operation Completed")
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def move(arg1,arg2):
    try:
        print("Moving " + arg1 + " to " + arg2)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            session.move(arg1,arg2)
        print("Operation Completed")
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def rm(rmDest):
    try:
        print("WARNING: This command deletes files recursively.")
        confirm = ""
        while confirm != "Y" and confirm != "N" and confirm != "y" and confirm != "n":
            confirm = input('Are you sure you want to delete ' + rmDest + '? [Y/N]')
        if confirm == "Y" or confirm == "y":
            with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
                sp.text = "Operation in Progress"
                connect()
                session.delete(rmDest)
            print("Deleted " + rmDest)   
        elif confirm == "N" or confirm == "n":
            print("Operation Canceled")
            sys.exit(0)
    except Exception as e: 
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def mkshare(arg1):
    try:
        print("Creating public share")
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            connect()
            share = session.share_file_with_link(shareDir)
        print("\n=== Created Share ==="+ bcolours.YELLOW + "\n\nLink: " + share.get_link() + "\nShare Contents: " + share.get_path() + "\n" + bcolours.DEFAULT)

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def rmshare(shareId):
    try:
        confirm = ""
        connect()
        output = session.get_shares(shareId)
        sharepath = ""
        for i in output:
            sharepath = i.get_path()
        if sharepath == "":
            print("Share not found")
        else:
            while confirm != "Y" and confirm != "N" and confirm != "y" and confirm != "n":
                confirm = input('Are you sure you want to delete share ' + sharepath + '? [Y/N]')
            if confirm == "Y" or confirm == "y":
                for i in output:
                    sp.text = "Operation in Progress"
                    session.delete_share(i.get_id())
            print("\nOperation Completed")

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

##### END COMMAND DEFINITIONS #####

def main():
    global dl_lpath #TODO: Find out what these are used for and get rid of them
    global dl_rpath

### Usage Menu Text

    title = "\n====\nncc_cli v" + version + "\n====\n"

    epilog = ""

### Non-Interactive Argument Parser

    parser = argparse.ArgumentParser(description=title, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter) #Create primary argument parser
    subparsers = parser.add_subparsers(dest='subparser') #Create subparsers for each command (eg. ls, get, put, etc)

    parser_ls = subparsers.add_parser('ls', help='list directory contents')
    parser_ls.add_argument('lsDir', help="<directory>", default="/", nargs="?")
    parser_ls.add_argument('-l', '--long', dest='longOutput', action='store_true')

    parser_put = subparsers.add_parser('put', help='upload file')
    parser_put.add_argument('localFile', help="<local file>")
    parser_put.add_argument('remoteDir', help="[remote directory]", default="/", nargs="?")

    parser_lsshare = subparsers.add_parser('lsshare', help='list shares')
    parser_lsshare.add_argument('lsDir', help="<directory>", default="/", nargs="?")

    parser_mkshare = subparsers.add_parser('mkshare', help='create file share')
    parser_mkshare.add_argument('shareDir', help="<directory>", default="/", nargs="?")

    parser_rmshare = subparsers.add_parser('rmshare', help='remove file share')
    parser_rmshare.add_argument('shareId', help="<directory>", default="/", nargs="?")

    parser_mkdir = subparsers.add_parser('mkdir', help='create new directory')
    parser_mkdir.add_argument('mkDir', help="<directory>", default="/", nargs="?")

    parser_rm = subparsers.add_parser('rm', help='delete file(s)')
    parser_rm.add_argument('rmDest', help="<directory>", default="/", nargs="?")

    try: #If no arguments are present, print usage output
        kwargs = vars(parser.parse_args())
        globals()[kwargs.pop('subparser')](**kwargs)
    except Exception as e:
        if (str(e) == "None"):
            parser.print_help()
            sys.exit(0)
        else: #Print useful exception message if we have one
            print("ERR: " + str(e) + "\n\nStack Trace:\n")
            print(traceback.format_exc())

def main_old():

    if (len(sys.argv) == 1) or (sys.argv[1] == "-h") or (sys.argv[1] == "--help"):
        t = Texttable()
        t.set_deco(t.VLINES)
        print ("No arguments provided.")
        print ("\nSyntax: " + sys.argv[0] + " [command] <arguments>\n")
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
        print (t.draw())
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
                print("Creates a new directory\nSyntax: mkdir <name>")
            else: 
                mkdir(sys.argv[2])

        elif sys.argv[1] == "rm":
            if len(sys.argv) == 2:
                print("Recursively deletes a file or directory\nSyntax: rm <name>")
            else: 
                rm(sys.argv[2])

        elif sys.argv[1] == "put":
            if len(sys.argv) == 2:
                print("Uploads a file\nSyntax: put [local source] <remote dest>")
            elif len(sys.argv) == 3:
                put(sys.argv[2])
            elif len(sys.argv) == 4:
                put(sys.argv[2],sys.argv[3])

        elif sys.argv[1] == "putdir":
            if len(sys.argv) == 2:
                print("Uploads a directory\nSyntax: putdir [local source] <remote dest>")
            elif len(sys.argv) == 3:
                putdir(sys.argv[2])
            elif len(sys.argv) == 4:
                putdir(sys.argv[2],sys.argv[3])

        elif sys.argv[1] == "get":
            if len(sys.argv) == 2:
                print ("Downloads a file\nSyntax: get [remote source] <local dest>")
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
                print("Downloads directory as zip archive\nSyntax: getdir [remote source] <local dest>")
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
                print ("Copies file within cloud\nSyntax: cp [source file] [destination dir]")
            elif len(sys.argv) == 4:
                copy(sys.argv[2],sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1])
        elif sys.argv[1] == "mv":
            if (len(sys.argv) == 2) or (len(sys.argv) == 3):
                print("Moves file within cloud\nSyntax: mv [source file] [destination dir]")
            elif len(sys.argv) == 4:
                move(sys.argv[2],sys.argv[3] + '/' + sys.argv[2].rsplit('/', 1)[-1])
        elif sys.argv[1] == "mkshare":
            if len(sys.argv) == 2:
                print("Creates new share with link from supplied file/directory\nSyntax: mkshare [remote file/dirname]")
            else: 
                mkshare(sys.argv[2])
        elif sys.argv[1] == "rmshare":
            if len(sys.argv) == 2:
                print("Deletes file share from supplied file/directory\nSyntax: rmshare [remote file/dirname]")
            else: 
                rmshare(sys.argv[2])
        else:
            print("Invalid Command, please revise.")
    else:
        print("Invalid Syntax, please revise.")

if __name__ == '__main__':
    try: 
        main()
    except KeyboardInterrupt:
        print("Operation Interrupted")
        sys.exit()
