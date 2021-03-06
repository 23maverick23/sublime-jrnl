import sublime, sublime_plugin
import os, fnmatch, re, time
import datetime
from pickle import load, dump
import subprocess
import json

def settings():
    return sublime.load_settings('jrnl.sublime-settings')

def get_config_path():
    return os.path.normpath(os.path.expanduser(settings().get("config_path")))

def load_and_fix_json(json_path):
    """Tries to load a json object from a file.
    If that fails, tries to fix common errors (no or extra , at end of the line).
    """
    try:
        with open(json_path) as f:
            json_str = f.read()
    except IOError as e:
        sublime.error_message("I/O error({0}): {1} : {2}".format(e.errno, json_path, e.strerror))
        return
    config =  None
    try:
        return json.loads(json_str)
    except ValueError as e:
        # Attempt to fix extra ,
        json_str = re.sub(r",[ \n]*}", "}", json_str)
        # Attempt to fix missing ,
        json_str = re.sub(r"([^{,]) *\n *(\")", r"\1,\n \2", json_str)
        try:
            config = json.loads(json_str)
            with open(json_path, 'w') as f:
                json.dump(config, f, indent=2)
            return config
        except ValueError as e:
            return False


class JrnlListCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        window = sublime.active_window()
        self.file_list = [];
        config = load_and_fix_json(get_config_path())
        if config:
            for j in config['journals']:

                if type(config['journals'][j]) is dict:
                    path = config['journals'][j]['journal']
                else:
                    path = os.path.expanduser(config['journals'][j])
                modified_str = time.strftime("Last modified: %d/%m/%Y %H:%M", time.gmtime(os.path.getmtime(path)));
                self.file_list.append([j,path, modified_str])

            self.file_list.sort(key=lambda item:  os.path.getmtime(item[1]), reverse=True)

        window.show_quick_panel( self.file_list, self.open_jrnl)

    def open_jrnl(self, index):
         if index == -1:
             return
         file_path = self.file_list[index][1]
         sublime.run_command("jrnl_open", {"file_path": file_path})


class JrnlOpenCommand(sublime_plugin.ApplicationCommand):

    def run(self, file_path):
        sublime.set_timeout(lambda: self.async_open(file_path) , 0)


    def async_open(self, file_path):
        view = sublime.active_window().open_file(file_path, sublime.ENCODED_POSITION)
        def set_syntax():
            if view.is_loading():
                sublime.set_timeout_async(set_syntax, 0.1)
            else:
                view.set_syntax_file("Packages/jrnl/jrnl.tmLanguage")
        set_syntax()
        view.set_read_only(True)


