# -*- coding:Utf-8 -*-

import os
import logging

def bash_escape(string):
    return string.replace('"', '\\"')

class BatchRenamer:
    def __init__(self):
        self.files = []
        self.cwd = os.getcwd()
    
    def append(self, old_url, new_name):
        old_name = os.path.dirname(old_url)
        new_url = os.path.join(os.path.dirname(old_url), new_name)
        if old_name != new_name:
            self.files.append((old_url, new_url))
    
    def do(self):
        for (old_url, new_url) in self.files:
            try:
                if os.path.exists(new_url):
                    logging.warning(new_url + " already exists")
                else:
                    os.rename(old_url, new_url)
            except OSError as err:
                logging.warning(str(err) + ": renaming \"" + old_url + "\" to \"" + new_url + "\"")
    
    def get_do_commands(self):
        do_commands = (u'mv -n "' + bash_escape(old_url) + u'" "' + bash_escape(new_url) + u'"' for (old_url, new_url) in self.files)
        return do_commands
        
    def get_undo_script_content(self):

        undo_string = u"\n    ".join(u'mv -n "' + bash_escape(new_url) + u'" "' + bash_escape(old_url) + u'"' for (old_url, new_url) in self.files)
        do_string = u"\n    ".join(u'mv -n "' + bash_escape(old_url) + u'" "' + bash_escape(new_url) + u'"' for (old_url, new_url) in self.files)
        
        script_content = u"#! /bin/sh"
        script_content = u"cd '" + self.cwd + u"'"
        script_content += u"""
if [ "$1" = "-d" ]
then
    """
        script_content += do_string
        script_content += u"""
else
    """
        script_content += undo_string
        script_content += """
fi
"""

        return script_content
    
    def create_undo_script(self, file_url):
        script_file = codecs.open(file_url, "w+", encoding='utf-8')
        script_file.write(self.get_undo_script_content())
