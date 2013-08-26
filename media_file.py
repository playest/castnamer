#! /usr/bin/env python
# -*- coding:Utf-8 -*-

import os
import re
import logging
from media_helpers import *
from media import *

class MediaFile:
    def __init__(self, url):
        if(os.path.exists(url)):
            self.url = url
        else:
            raise IOError("No such file or directory: " + url)
        
        almost_base_name, self.file_extension = os.path.splitext(self.url)
        self.base_name = os.path.basename(almost_base_name)
        self.file_name = self.base_name + self.file_extension
        
        regex = u"(.*?)((?:\.en|\.fr|\.eng|\.fre)*)(\.avi|\.mp4|\.mkv|\.flv|\.srt|\.sub|\.ass|$)"
        parts = re.split(regex, self.file_name)
        self.file_name_wo_exts = parts[1]
        self.lang_ext = parts[2]
        self.ext = parts[3]
        
        self.media = None
    
    def make_media_movie(self, browser, forced_title=None):
        if re.search(u"(?:[Ss]|[-._ ]?[Ss]eason[-._ ]?)(?:\d?\d)(?:[Eex]|[-._ ]?[Ee]pisode[-._ ]?)(?:\d\d)", self.file_name_wo_exts) != None:
            logging.warning("looks like a tv series, rejected from movies")
            return False
            
        regex = u"^(.*?)(?:(?:[-._](?! ))|[ ]|$)(?:(?:\(?((?:19|20)\d\d)\)?)?[-._ ]+(.*?))?(\d*)$"
        parts = re.split(regex, self.file_name_wo_exts)
        logging.debug(parts)
        if len(parts) == 6:
            title = smart_remove_char(parts[1]) if forced_title is None else (forced_title)
            year = parts[2]
            number = parts[4]
            logging.info(("movie", title, year, number, self.file_name_wo_exts))
            self.media = Media()
            self.media.title = title
            self.media.type_ = ""
            #self.media.first_year = year
            matching_medias = browser.search2(self.media)
            #logging.debug((u"matching_medias = " , str(matching_medias)))
            if matching_medias != []:
                self.media = matching_medias[0]
                if re.search(number + "$", self.media.title) == None:
                    self.media.title += " " + number
            else:
                return False
            return True
        else:
            return False
    
    def make_media_series(self, browser, search=1, forced_title=None):
        #((?:19|20)\d\d)
        if search == 2:
            regex = u"^(?:(.*?)[-._ ]{1,3}(?:((?:20|19)\d\d)[-._ ]{1,3})?)" + ("?" if forced_title else "") + "(?:[Ss]|[-._ ]?[Ss]eason[-._ ]?)?(\d?\d)(?:[Eex]|[-._ ]?[Ee]pisode[-._ ]?)?(\d\d)(?:[-._ ]{1,3}(.*))?$"
        else:
            regex = u"^(.*?)[-._ ]{1,3}(?:((?:20|19)\d\d)[-._ ]{1,3})?(?:[Ss]|[-._ ]?[Ss]eason[-._ ]?)?(\d?\d)(?:[Eex]|[-._ ]?[Ee]pisode[-._ ]?)(\d\d)(?:[-._ ]{1,3}(.*))?$"
        parts = re.split(regex, self.file_name_wo_exts)
        logging.debug(parts)
        logging.debug(len(parts))
        
        if len(parts) == 7:
            title = smart_remove_char(parts[1]) if not forced_title else forced_title
            year = parts[2]
            season_num = parts[3]
            episode_num = parts[4]
            logging.info(("series", title, year, season_num, episode_num, self.file_name_wo_exts))
            parent_show = Media()
            parent_show.title = title
            parent_show.type_ = "tv series"
            #parent_show.first_year = year
            if search == 2:
                logging.debug("search 2")
                matching_medias = browser.search2(parent_show)
            else:
                logging.debug("search 1")
                matching_medias = browser.search(parent_show)
            logging.debug("len(matching_medias) = " + str(len(matching_medias)))
            if matching_medias != []:
                parent_show = matching_medias[0]
                browser.find_seasons(parent_show)
                parent_show.browser = browser
                #browser.find_episodes(parent_show)
                
                searched_episode = Episode(parent_show, season_num, episode_num)
                episode = parent_show.get_submedia(searched_episode)
                if episode != None:
                    self.media = episode
                    logging.info(self.media)
                else:
                    logging.warning("failed search, fallback on local info")
                    episode = searched_episode
                    parent_show.add_submedia(episode)
                    self.media = episode
                    return True
            else:
                return False
            return True
        else:
            return False
    
    def make_media_fallback(self):
        self.media = None
        logging.warning("Cannot find reliable data for " + self.file_name_wo_exts)
        return False
    
    def make_media(self, browser, forced_title=None):
        if not self.make_media_series(browser, forced_title=forced_title):
            if not self.make_media_movie(browser, forced_title):
                if not self.make_media_series(browser, 2, forced_title):
                    self.make_media_fallback()
        
    def get_normalized_name(self):
        return self.media.get_normalized_name() + self.lang_ext + self.ext
    
    @staticmethod
    def read_list(list_):
        media_files = []
        for f in list_:
            media_files.append(MediaFile(f))
        return media_files

    def __repr__(self):
        return "<MediaFile  " + self.url + ">"
