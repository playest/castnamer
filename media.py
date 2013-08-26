#! /usr/bin/env python
# -*- coding:Utf-8 -*-

import urlparse
import logging

class Media:
    def __init__(self, title = u""):
        self.matched_attr = [u"title", u"first_year"]
        self.title = title
        self.first_year = u""
        self.year = u""
        self.type_ = u""
        self.season = u""
        self.number = u""
        self.url = u""
        self.identifier = u""
        
        self.browser = None
        
        self.seasons = None
        self.cached_seasons = []
        self._submedias = {}
    
    def get_key(self):
        return (self.title.lower(),)
    
    def add_submedia(self, media):
        self._submedias[media.get_key()] = media
    
    def get_submedia(self, media):
        if media.get_key() in self._submedias:
            return self._submedias[media.get_key()]
        else:
            if self.seasons != None and self.seasons != []:
                if media.season_num not in self.cached_seasons:
                    self.cached_seasons.append(media.season_num)
                    logging.debug("loading episodes of season " + media.season_num)
                    self.browser.find_episodes_of_season(self, int(media.season_num))
                    logging.debug(self._submedias)
                    if media.get_key() in self._submedias:
                        return self._submedias[media.get_key()]
                    else:
                        return None
                else:
                    return None
            else:
                return None
    
    def get_absolute_url(self):
        s = urlparse.urljoin("http://www.imdb.com/", self.url)
        return s
    
    def get_normalized_type(self):
        return self.type_.replace(" ", "_").lower()
    
    def get_normalized_name(self):
        return self.title
    
    def match(self, media):
        for attr in self.matched_attr:
            if getattr(media, attr) != "" and getattr(self, attr) != "":
                if getattr(self, attr) != getattr(media, attr):
                    return False
        return True
    
    def __eq__(self, media):
        for attr in self.matched_attr:
            if getattr(self, attr) != getattr(media, attr):
                return False
        return True
    
    def __lt__(self, media):
        for attr in self.matched_attr:
            if getattr(media, attr) != "":
                if type(getattr(media, attr)) == str:
                    if getattr(self, attr).lower() != getattr(media, attr).lower():
                        return False
                else:
                    if getattr(self, attr) != getattr(media, attr):
                        return False
        return True
    
    def __gt__(self, media):
        for attr in self.matched_attr:
            if getattr(media, attr) != "":
                if type(getattr(media, attr)) == str:
                    if getattr(self, attr).lower() != getattr(media, attr).lower():
                        return False
                else:
                    if getattr(self, attr) != getattr(media, attr):
                        return False
        return True
    
    
    def __repr__(self, level=0):
        s = u"<Media title="
        s += self.title
        s += u", first_year="
        s += str(self.first_year)
        s += u", type="
        s += self.type_
        s += u", url="
        s += self.url
        s += u", submedias=["
        if self._submedias != []:
            s += ("\n" + ("    " * (level + 1))).join([self._submedias[m].__repr__() for m in self._submedias])
        s += u"]>"
        
        return s

class Episode(Media):
    def __init__(self, parent_show, season_num, episode_num):
        Media.__init__(self)
        self.show = parent_show
        self.season_num = season_num
        self.episode_num = episode_num
        self.title = u""
    
    def get_key(self):
        if self.season_num is None:
            return (self.show.title, -10, int(self.episode_num))
        else:
            return (self.show.title, int(self.season_num), int(self.episode_num))
            
    def get_normalized_name(self):
        if self.title != "":
            return self.show.title + " - " + "S{:>02}E{:>02}".format(*(self.season_num, self.episode_num)) + " - " + self.title
        else:
            return self.show.title + " - " + "S{:>02}E{:>02}".format(*(self.season_num, self.episode_num))
        
    def __repr__(self):
        try:
            s = "<Episode season="
            s += str(self.season_num)
            s += ", episode="
            s += str(self.episode_num)
            s += ", title="
            s += self.title
            s += ">"
        except (UnicodeEncodeError, UnicodeDecodeError):
            s = "[Bad unicode data]"
        return s
