# This file contains commands which can be executed as part of ncc requests
import humanize,multiprocessing
from yaspin import yaspin
from yaspin.spinners import Spinners
from texttable import Texttable
from ncc_cli.connection import *
from ncc_cli.transfer import *

def ls(lsDir,longOutput=False):
    try:
        session = connect()
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
        session = connect()
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

def put(localFile,remoteDir='/'):
    try:
        print("Uploading " + localFile)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            session = connect()
            session.put_file(remoteDir,localFile)
        print("Upload Complete")

    except Exception as e:
        print("Error: could not upload file:\n" + str(e))
    # TODO: Better progress indication. Need library update for this.

def putdir(localDir,remoteDir='/'):
    try:
        print("Uploading directory " + localDir)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            session = connect()
            session.put_directory(remoteDir,localDir)
        print("Upload Complete")

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())
    # TODO: Better progress indication. Need library update for this.

def get(remoteFile,localDir=None):
    try:
        session = connect()
        fileSize = dl_getsize(session, remoteFile)
        copy = multiprocessing.Process(name='copy', target=getproc(session, localDir, remoteFile))
        prog = multiprocessing.Process(name='prog', target=dl_progress(fileSize, localDir))
        copy.start()
        prog.start()
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def getdir(remoteDir,localDir=None):

    if localDir == None or localDir == '.':
        localDir = './' + os.path.basename(remoteDir) + '.zip'
    try:
        session = connect()
        getdir_prog = multiprocessing.Process(name='prog', target=zip_dl_progress(session, localDir, remoteDir))
        getdir_prog.start()
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def mkdir(mkDir):
    try:
        session = connect()
        session.mkdir(mkDir)
        print("created " + mkDir)
    except Exception as e: 
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def cp(sourceFile,destinationFile):
    try:
        print ("Copying " + sourceFile + " to " + destinationFile)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            session = connect()
            session.copy(sourceFile,destinationFile)
        print("Operation Completed")
    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def mv(sourceFile,destinationFile):
    try:
        print("Moving " + sourceFile + " to " + destinationFile)
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            session = connect()
            session.move(sourceFile,destinationFile)
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
                session = connect()
                session.delete(rmDest)
            print("Deleted " + rmDest)   
        elif confirm == "N" or confirm == "n":
            print("Operation Canceled")
            sys.exit(0)
    except Exception as e: 
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def mkshare(shareDir):
    try:
        print("Creating public share")
        with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
            sp.text = "Operation in Progress"
            session = connect()
            share = session.share_file_with_link(shareDir)
        print("\n=== Created Share ==="+ bcolours.YELLOW + "\n\nLink: " + share.get_link() + "\nShare Contents: " + share.get_path() + "\n" + bcolours.DEFAULT)

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())

def rmshare(shareId):
    try:
        confirm = ""
        session = connect()
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
                    with yaspin(Spinners.bouncingBall, attrs=["bold"],) as sp:
                        sp.text = "Operation in Progress"
                        session.delete_share(i.get_id())
            print("\nOperation Completed")

    except Exception as e:
        print("ERR: " + str(e) + "\n\nStack Trace:\n")
        print(traceback.format_exc())