#! /usr/bin/env python
# -*- coding:Utf-8 -*-

import os
import logging
import sys
import argparse
import shutil
import time

from page_loader import PageLoader
from imdb_browser import IMDBBrowser
from media_file import MediaFile
from batch_renamer import BatchRenamer

def setuplogging(log_file_url, loglevel, printtostdout):
    #print "starting up with loglevel",loglevel,logging.getLevelName(loglevel)
    logging.basicConfig(filename=log_file_url, level=loglevel)
    if printtostdout:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(soh)

def has_media_extension(file_url):
    media_extensions = ["avi", "mp4", "flv", "mkv", "srt"]
    return os.path.splitext(file_url)[1][1:] in media_extensions

def listdir_by_date(dir_url, prefix=""):
    files = []
    for f in os.listdir(dir_url):
        if f.startswith(prefix):
            stats = os.stat(os.path.join(dir_url, f))
            lastmod_date = time.localtime(stats[8])
            date_file_tuple = (lastmod_date, f)
            files.append(date_file_tuple)
    files.sort()
    files.reverse()
    return files

def main():
    loglevel = {
        "critical" : logging.CRITICAL,
        "error" : logging.ERROR,
        "warning" : logging.WARNING,
        "info" : logging.INFO,
        "debug" : logging.DEBUG,
    }
    
    home_dir_url = unicode(os.getenv("HOME"))
    default_conf_dir = os.path.join(home_dir_url, u".castnamer")
    default_cache_dir = os.path.join(home_dir_url, u".castnamer", u"cache")
    
    # option pour faire des links au lieu de renommer
    # option pour filtrer uniquement sur les directories, cad qu'un truc précisé avec -f sera toujours traité qqs sont ext
    # option pour maj le cache
    parser = argparse.ArgumentParser(description='castnamer is a program to help rename all your media files.')
    parser.add_argument('-f', '--files', dest="files2", nargs="+", default=[], metavar="FILES", help="You can also select the files you want to treat with this option")
    parser.add_argument('files', nargs="*", default=[], help="treat these media files, without the --all option it will exclude all files that does not have a media extension")
    parser.add_argument('-d', '--dirs', nargs="+", default=[], help='treat all the media files in these directories, with the --ext option ALL the files will be treated')
    parser.add_argument('-r', '--dry-run', action='store_true', help='do not rename the files')
    parser.add_argument('-s', '--script', metavar="SCRIPT URL", action='store', nargs="?", default=False, const=True, help="force the generation of the do/undo script (during a dry run for example), you can optionnaly select a url for the script, if the current call is not a dry run a do/undo script will always be generated in " + default_conf_dir)
    parser.add_argument('-t', '--title', help='force the title of the parent media (useful for tv series)')
    parser.add_argument('-a', '--all', action='store_true', help='if set, ALL the files in the directories given with the --dirs options will be treated, otherwise, ONLY the files with media extensions will be treated')
    parser.add_argument('-i', '--ignore-well-named', action='store_true', help='do not treat files that look well named')
    parser.add_argument('-c', '--clear-cache', action='store_true', help='clear the cache before running')
    parser.add_argument('-l', '--force-load', action='store_true', help="force the loading of every request, the cache won't be updated not cleared")
    parser.add_argument('-u', '--undo', action='store_true', help="undo the changes corresponding to the last run of this program by running the most recent undo script in " + default_conf_dir)
    
    parser.add_argument('--conf-dir', default=default_conf_dir, help="set the conf directory, by default it's %(default)s")
    parser.add_argument('--cache-dir', default=default_cache_dir, help="set the cache directory, by default it's %(default)s")
    
    group_verbosity = parser.add_mutually_exclusive_group()
    group_verbosity.add_argument('-v', '--verbosity', metavar="LEVEL", action='store', nargs="?", choices=loglevel.keys(), const="debug", default="warning", help="set the verbosity level, it's \"warning\" by default and \"debug\" when the flag is set without parameter")
    group_verbosity.add_argument('-q', '--quiet', action='store_true', help='do not display anything')
    
    # Read the args
    args = parser.parse_args()
    
    args.title = unicode(args.title) if args.title else None
    args.cache_dir = unicode(args.cache_dir)
    args.conf_dir = unicode(args.conf_dir)
    args.files = [f.decode("utf8") for f in args.files]
    args.files2 = [f.decode("utf8") for f in args.files2]
    
    if args.undo:
        script_urls = listdir_by_date(args.conf_dir, u"undo")
        if script_urls != []:
            last_undo_script_url = script_urls[0][1]
            os.system('bash "' + os.path.join(args.conf_dir, last_undo_script_url) + '"')
            exit()
    
    # Creation of directories
    if not os.path.exists(args.conf_dir):
        os.mkdir(args.conf_dir)
    
    if not os.path.exists(args.cache_dir):
        os.mkdir(args.cache_dir)
    
    # Logs
    if args.quiet:
        setuplogging(os.path.join(args.conf_dir, "castnamer.log"), loglevel["debug"], False)
    else:
        setuplogging(os.path.join(args.conf_dir, "castnamer.log"), loglevel[args.verbosity], True)
    
    logging.debug("args = " + str(args).replace(", ", "\n").replace("(", "\n").replace(")", "\n"))
    
    # Cache
    if args.clear_cache:
        shutil.rmtree(args.cache_dir)
        os.mkdir(args.cache_dir)
    
    # make page loader
    if args.force_load:
        loader = PageLoader()
    else:
        loader = PageLoader(args.cache_dir)
    
    # make list of files to treat
    files = []
    for d in args.dirs:
        for f in os.listdir(unicode(d)):
            if args.all or has_media_extension(f):
                files.append(os.path.join(d, f))
    
    for f in args.files + args.files2:
        if args.all or has_media_extension(f):
            files.append(f)
    
    batch_renamer = BatchRenamer()
    imdbbrowser = IMDBBrowser(loader)
    
    media_files = MediaFile.read_list(files)
    
    for mf in media_files:
        mf.make_media(imdbbrowser, args.title)
        if mf.media is not None:
            if mf.file_name != mf.get_normalized_name():
                batch_renamer.append(mf.url, mf.get_normalized_name())
    
    default_script_storage_url = os.path.join(args.conf_dir, "undo_" + time.strftime("%d-%b-%Y_%H:%M:%S") + ".sh")
    
    if args.dry_run:
        print("\n".join(batch_renamer.get_do_commands()))
        if args.script == True:
            batch_renamer.create_undo_script(default_script_storage_url)
        elif type(args.script) == str:
            batch_renamer.create_undo_script(args.script)
    else:
        logging.debug("\n".join(batch_renamer.get_do_commands()))
        #batch_renamer.create_undo_script(default_script_storage_url)
        if type(args.script) == str:
            batch_renamer.create_undo_script(args.script)
        batch_renamer.do()
    
    # ignore_well_named à faire ...

class fake_logging:
    @staticmethod
    def debug(a):
        print a
    def critical(a):
        print a
    def info(a):
        print a
    def warning(a):
        print a
    def error(a):
        print a

if __name__ == "__main__":
    #from kitchen.text.converters import getwriter    
    #UTF8Writer = getwriter('utf8')
    #sys.stdout = UTF8Writer(sys.stdout)
    #logging.debug = fake_logging.debug
    main()

