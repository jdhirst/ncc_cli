#!/usr/bin/python3

# This is the main script which is called when the user executes an 'ncc' command

import sys,os,subprocess,configparser,time,argparse,traceback

# Import modular code (the monolithic script was very complicated and difficult to maintain)
from ncc_cli.commands import *
from ncc_cli.utils import *

version = "0.0.7" #Define current version

def main():
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

    parser_putdir = subparsers.add_parser('putdir', help='upload directory')
    parser_putdir.add_argument('localDir', help="<local directory>")
    parser_putdir.add_argument('remoteDir', help="[remote directory]", default="/", nargs="?")

    parser_get = subparsers.add_parser('get', help='download file')
    parser_get.add_argument('remoteFile', help="<remote file>")
    parser_get.add_argument('localDir', help="[local directory]", default=".", nargs="?")

    parser_getdir = subparsers.add_parser('getdir', help='download directory')
    parser_getdir.add_argument('remoteDir', help="<remote directory>")
    parser_getdir.add_argument('localDir', help="[local directory]", default=".", nargs="?")

    parser_cp = subparsers.add_parser('cp', help='copy files on server')
    parser_cp.add_argument('sourceFile', help="<source file>")
    parser_cp.add_argument('destinationFile', help="<destination file>", nargs="?")

    parser_mv = subparsers.add_parser('mv', help='move files on server')
    parser_mv.add_argument('sourceFile', help="<source file>")
    parser_mv.add_argument('destinationFile', help="<destination file>", nargs="?")

    parser_mkdir = subparsers.add_parser('mkdir', help='create new directory')
    parser_mkdir.add_argument('mkDir', help="<directory>", default="/", nargs="?")

    parser_rm = subparsers.add_parser('rm', help='delete file(s)')
    parser_rm.add_argument('rmDest', help="<directory>", default="/", nargs="?")

    parser_mkshare = subparsers.add_parser('mkshare', help='create file share')
    parser_mkshare.add_argument('shareDir', help="<directory>", default="/", nargs="?")

    parser_lsshare = subparsers.add_parser('lsshare', help='list shares')
    parser_lsshare.add_argument('lsDir', help="<directory>", default="/", nargs="?")

    parser_rmshare = subparsers.add_parser('rmshare', help='remove file share')
    parser_rmshare.add_argument('shareId', help="<directory>", default="/", nargs="?")

    try: #If no arguments are present, print usage output
        kwargs = vars(parser.parse_args())
        globals()[kwargs.pop('subparser')](**kwargs)
    except Exception as e:
        if (str(e) == "None"):
            initializeConfig() #Check if a configuration file exists already, if not, lets create one
            parser.print_help()
            sys.exit(0)
        else: #Print useful exception message if we have one
            print("ERR: " + str(e) + "\n\nStack Trace:\n")
            print(traceback.format_exc())

if __name__ == '__main__':
    try: 
        main()
    except KeyboardInterrupt:
        print("Operation Interrupted")
        sys.exit()
