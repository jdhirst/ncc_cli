# This file contains useful functions dealing with file transfers
import time,multiprocessing,os,traceback
from ncc_cli.connection import *
from tqdm import tqdm

def dl_getsize(session, dl_rpath):
    fobj = session.file_info(dl_rpath)
    return fobj.get_size()

def dl_progress(dl_rsize, dl_lpath):
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

def zip_dl_progress(session, dl_lpath, dl_rpath):
    if os.path.exists(dl_lpath):
        print(dl_lpath + " already exists")
    else:
        try:
            print("Downloading zip of " + dl_rpath)
            dl_lsize = 1
            getdir_copy = multiprocessing.Process(name='getdir_copy', target=getdirproc(session, dl_lpath, dl_rpath))
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

def getproc(session, dl_lpath, dl_rpath):
    try:
        print("Downloading " + dl_rpath)
        session.get_file(dl_lpath,dl_rpath)
        print("Download Complete")
    except Exception as e:
        print("Error: could not download file:\n" + str(e))

def getdirproc(session, dl_lpath, dl_rpath):
    try:
        session.get_directory_as_zip(dl_rpath, dl_lpath)
    except Exception as e:
        print("Error: could not download zip file:" + e)