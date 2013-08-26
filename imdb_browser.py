# -*- coding:Utf-8 -*-

"""
gérer les _
si le nom du fichier commence et fini par ", on retire les "
"""

from media import *
from media_helpers import *

import logging
import urllib
import urllib2

def parse_season_episode_string(str_):
    """Transform a string with season and episode number into a tuple (season_num, episode_num)"""
    season_num = None
    search_season_num = re.search("(S|s)([0-9]*)", str_)
    if search_season_num is not None:
        search_season_num = search_season_num.groups()
        if len(search_season_num) > 1:
            season_num = int(search_season_num[1])
    
    search_season_num = re.search("^([0-9]*)", str_)
    if search_season_num is not None:
        search_season_num = search_season_num.groups()
        if len(search_season_num) > 1:
            season_num = int(search_season_num[1])
    
    if season_num is None:
        season_num = -1
    
    episode_num = None
    search_episode_num = re.search("(Ep|E|EP|x|e)([0-9]*)", str_)
    if search_episode_num is not None:
        search_episode_num = search_episode_num.groups()
        if len(search_episode_num) > 1:
            episode_num = int(search_episode_num[1])
    
    if episode_num is None:
        episode_num = -1
    
    return (season_num, episode_num)

def make_season_episode_string(season_num, episode_num):
    return "S" + str(season_num) + "E" + str(episode_num)

class IMDBBrowser:
    def __init__(self, loader, force_title=None):
        self.cache = {}
        self.loader = loader
        self.force_title = force_title
        
    def search(self, media):
        logging.debug("search 1 : " + unicode(media))
        if media.get_key() not in self.cache:
            if media.type_ != "":
                type_part = u"&title_type=" + media.get_normalized_type()
            else:
                type_part = u""
            
            try:
                url = u"http://www.imdb.com/search/title?sort=moviemeter,asc&title=" + urllib.quote_plus(media.title.encode("utf-8")) + type_part
                etree_document = self.loader.load_and_parse_page(url)
                
                medias = []
                results = etree_document.xpath('//table[@class="results"]//td[@class="title"]')
                for r in results:
                    if r is not None:
                        m = Media()
                        title_link = r.xpath('a')[0]
                        m.title = smart_remove_char(title_link.text)
                        m.url = title_link.attrib["href"]
                        m.identifier = m.url.split("/")[2]
                        
                        year_type = r.xpath('span[@class="year_type"]')[0].text[1:-1].split(" ", 1)
                        if len(year_type) >= 1:
                            m.first_year = year_type[0]
                        if len(year_type) >= 2:
                            m.type_ = year_type[1]
                        
                        if m > media:
                            if m.title.lower() == media.title.lower():
                                i = 0
                                while i < len(medias) and m.title.lower() == medias[i].title.lower():
                                    i = i + 1
                                medias.insert(i, m)
                            else:
                                medias.append(m)
                self.cache[media.get_key()] = medias
                return medias
            except urllib2.HTTPError as err:
                logging.debug(str(err))
                medias = []
                self.cache[media.get_key()] = medias
                return []
        else:
            return self.cache[media.get_key()]
    
    def search2(self, media):
        url = u"http://www.imdb.com/find?q=" + urllib.quote_plus(media.title.encode("utf-8"))
        logging.debug("search 2 : " + unicode(media))
        etree_document = self.loader.load_and_parse_page(url)
        results = etree_document.xpath('//table//a[starts-with(@href, "/title/tt") and text() != ""]/..')
        medias = []
        for r in results:
            if r is not None:
                m = Media()
                title_link = r.xpath(".//a")[0]
                m.title = smart_remove_char(title_link.text)
                m.url = title_link.attrib["href"]
                m.identifier = m.url.split("/")[2]
                medias.append(m)
                
        return medias
    
    def find_seasons(self, media):
        if media.seasons is None:
            url = media.get_absolute_url()
            etree_document = self.loader.load_and_parse_page(url)
            seasons = etree_document.xpath('//h4[text()="Season:"]/..//a/text()')
            media.seasons = seasons
        return media.seasons
        
    
    def find_episodes_of_season(self, media, season):
        key = (media.title, season)
        if key not in self.cache:
            url = "http://www.imdb.com" + media.url + "episodes?season=" + str(season)
            etree_document = self.loader.load_and_parse_page(url)
            episodes_elements = etree_document.xpath('//div[@class="list detail eplist"]/div')
            
            for episode_element in episodes_elements:
                season_episode_string = episode_element.xpath('div[@class="image"]/a/div/div/text()')[0]
                (season_num, episode_num) = parse_season_episode_string(season_episode_string)
                epi = Episode(media, season_num, episode_num)
                link_to_episode = episode_element.xpath(".//a[@itemprop='name']")[0]
                title = smart_remove_char(link_to_episode.text)
                epi.title = title
                
                url = link_to_episode.attrib["href"]
                epi.url = url
                
                media.add_submedia(epi)
            
            self.cache[key] = media._submedias
        else:
            media._submedias = self.cache[key]
            
    def find_episodes(self, media, seasons="all"):
        if seasons == "all":
            selected_seasons = media.seasons
        else:
            selected_seasons = seasons
        
        for s in selected_seasons:
            self.find_episodes_of_season(media, s)
