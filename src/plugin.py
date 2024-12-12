#  -*- coding: utf-8 -*-
#  CheckPyCode
#  Code by Vasiliks

import sys
import os
import re
import time
from . import _, getSkin,  ScreenWidth
from Components.ActionMap import ActionMap
from Components.config import config, ConfigText, ConfigSubsection, getConfigListEntry, ConfigYesNo, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.FileList import FileList
from Plugins.Plugin import PluginDescriptor
import Plugins.Extensions.CheckPyCode.pycodestyle as pcstyle
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

PV = '1.0'
config.plugins.checkpycode = ConfigSubsection()
config.plugins.checkpycode.current_path = ConfigText(default="/", visible_width=70, fixed_size=False)
config.plugins.checkpycode.remember_last_path = ConfigYesNo(default=False)
config.plugins.checkpycode.max_line_length = ConfigInteger(default=79, limits=(70, 160))
config.plugins.checkpycode.show_pep8 = ConfigYesNo(default=False)
config.plugins.checkpycode.show_source = ConfigYesNo(default=False)


def convert_bytes(size):
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0


def file_size(file_path):
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)


def info_py_file(file_path):
    if os.path.exists(file_path):
        return "{} {}".format(
            file_size(file_path),
            time.ctime(os.path.getmtime(file_path)))
    return ""


def python_version():
    return sys.version.split('[')[0].strip()


full_version = 'Python: {}?Pycodestyle: {}'.format(python_version(), pcstyle.__version__)


class CheckPyCode(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = getSkin("CheckPyCode")
        self.session = session
        self.setTitle(_('Plugin CheckPyCode ver.' + PV))
        current_path = config.plugins.checkpycode.current_path.value
        hide = ['/dev', '/dev.static', '/ram', '/proc', '/sys', '/home', '/run']
        self['filelist'] = FileList(current_path, matchingPattern=r"^.*\.(py)",
                                    useServiceRef=False,
                                    inhibitDirs=hide)
        self['key_red'] = Label(_('Exit'))
        self['filetocheck'] = Label(current_path)
        self['infopyfile'] = Label()
        self['checkinfo'] = Label()
        self['full_ver'] = ScrollLabel(full_version)
        self.check = True
        self.detailed = ""
        self['actions'] = ActionMap(['CheckPyCodeActions'],
                                    {'ok': self.ok,
                                     'cancel': self.exit,
                                     'red': self.exit,
                                     'info': self.about,
                                     'menu': self.menu,
                                     'up': self.up,
                                     'down': self.down,
                                     'left': self.left,
                                     'right': self.right
                                     }, -1)

    def menu(self):
        self.session.open(CheckPyCodeConf)

    def up(self):
        self['filelist'].up()
        self.cross()

    def down(self):
        self['filelist'].down()
        self.cross()

    def left(self):
        self['filelist'].pageUp()
        self.cross()

    def right(self):
        self['filelist'].pageDown()
        self.cross()

    def cross(self):
        self.check = True
        if self['filelist'].canDescent():
            self['checkinfo'].setText('No data')
            self['filetocheck'].setText(self['filelist'].getCurrentDirectory())
            self['infopyfile'].setText(' ')
        else:
            path = '{}{}'.format(
                    self['filelist'].getCurrentDirectory(),
                    self['filelist'].getFilename())
            self['checkinfo'].setText(' ')
            self['filetocheck'].setText(path)
            self['infopyfile'].setText(info_py_file(path))

    def show_pep8(self):
        if self.detailed:
            self.session.open(Detailed, self.detailed)

    def ok(self):
        if self.check:
            if self['filelist'].canDescent():
                self['filelist'].descent()
                self['checkinfo'].setText('No data')
                self['filetocheck'].setText(self['filelist'].getCurrentDirectory())
                self['infopyfile'].setText(' ')
            else:
                file_to_check = self['filelist'].getFilename()
                path = '{}{}'.format(self['filelist'].getCurrentDirectory(), file_to_check)
                self['checkinfo'].setText('Please wait!')
                self['filetocheck'].setText(path)
                self['infopyfile'].setText(info_py_file(path))

                if file_to_check.endswith('.py'):
                    self.check_pep8(
                        path,
                        max_line_length=config.plugins.checkpycode.max_line_length.value,
                        show_pep8=config.plugins.checkpycode.show_pep8.value,
                        show_source=config.plugins.checkpycode.show_source.value)
        else:
            self.check = True
            self.session.open(Detailed, self.detailed)

    def check_pep8(self, file_path, **kwargs):
        style_guide = pcstyle.StyleGuide(kwargs)
        result = style_guide.check_files([file_path])
        errors = ""
        errors += '\tProcessing speed:\n'
        if result.elapsed:
            for key in result._benchmark_keys:
                errors += ('%-7d %s per second (%d total)' % (result.counters[key] / result.elapsed, key, result.counters[key])) + "\n"
        errors += '{:<7.2f} {}'.format(result.elapsed, 'seconds elapsed\n\n')

        if result.total_errors > 0:
            errors += '\tStatistics errors and warnings:\n'
            for error in result.get_statistics():
                errors += error + "\n"
        self['checkinfo'].setText(errors)

        detailed = ""
        for line_number, offset, code, text, doc in result._deferred_print:
            detailed += config.plugins.checkpycode.max_line_length.value * "—" + "\n"
            detailed += "{}\n".format(result._fmt % {
                'path': result.filename,
                'row': result.line_offset + line_number, 'col': offset + 1,
                'code': code, 'text': text,
                })
            detailed += "\n"
            if result._show_source:
                if line_number > len(result.lines):
                    line = ''
                else:
                    line = result.lines[line_number - 1]
                detailed += "{}\n".format(line.rstrip())
                detailed += "{}\n\n".format(re.sub(r'\S', '_', line[:offset]) + '^')
            if result._show_pep8 and doc:
                detailed += ('\t{}\n').format(doc.strip())
        self.detailed = detailed
        self.check = False

    def exit(self):
        if config.plugins.checkpycode.remember_last_path.value:
            curr_parh = self['filelist'].getCurrentDirectory()
            config.plugins.checkpycode.current_path.value = curr_parh
        else:
            config.plugins.checkpycode.current_path.value = "/"
        config.plugins.checkpycode.save()
        self.close()

    def about(self):
        self.session.open(
            MessageBox,
            _('Tool to check your Python code \nEnigma2 plugin ver.%s\n©2024 Vasiliks') %
            PV,
            MessageBox.TYPE_INFO,
            simple=True)


class Detailed(Screen):
    def __init__(self, session, detailed):
        Screen.__init__(self, session)
        self.skin = getSkin("Detailed")
        self.detailed = detailed
        self.setTitle('\tDetailed Information')
        self['key_red'] = Label(_('Exit'))
        self['full_ver'] = ScrollLabel(full_version)
        self['checkinfo'] = ScrollLabel(_(''))
        self["actions"] = ActionMap(["CheckPyCodeActions"],
                                    {
                                     "cancel": self.close,
                                     'ok': self.close,
                                     "up": self["checkinfo"].pageUp,
                                     "down": self["checkinfo"].pageDown,
                                     }, -1)

        self.onShow.append(self.readfilerez)

    def readfilerez(self):
        if self.detailed:
            self['checkinfo'].setText(self.detailed)
        else:
            self['checkinfo'].setText(' ')


class CheckPyCodeConf(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = getSkin("CheckPyCodeConf")
        self.session = session
        self['key_red'] = Label(_('Cancel'))
        self['key_green'] = Label(_('Save'))
        self.setTitle(_('Settings'))
        ConfigListScreen.__init__(self, [
         getConfigListEntry(_('Remember last path:'), config.plugins.checkpycode.remember_last_path),
         getConfigListEntry(_('Max line length:'), config.plugins.checkpycode.max_line_length),
         getConfigListEntry(_('Show source:'), config.plugins.checkpycode.show_source),
         getConfigListEntry(_('Show pep8:'), config.plugins.checkpycode.show_pep8),
         getConfigListEntry(_('Current path:'), config.plugins.checkpycode.current_path)])
        self['actions'] = ActionMap(['CheckPyCodeActions'],
                                    {
                                     'ok': self.save,
                                     'green': self.save,
                                     'cancel': self.exit,
                                     'red': self.exit
                                     }, -2)

    def save(self):
        for x in self['config'].list:
            x[1].save()
        from Components.PluginComponent import plugins
        plugins.reloadPlugins()
        self.close()

    def exit(self):
        for x in self['config'].list:
            x[1].cancel()
        self.close()


def main(session, **kwargs):
    session.open(CheckPyCode)


def Plugins(path, **kwargs):
    return PluginDescriptor(name=_('CheckPyCode'),
                            description=_('Tool to check your Python code ver.' + PV),
                            icon='checkpycode.png',
                            where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
