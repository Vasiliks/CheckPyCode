# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import getDesktop
from gettext import bindtextdomain, dgettext, gettext
from os import environ, path

try:
    import xml.etree.cElementTree as ETree
except ImportError:
    import xml.etree.ElementTree as ETree


def localeInit():
    environ["LANGUAGE"] = language.getLanguage()[:2]
    bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, "Extensions/CheckPyCode/locale"))


def _(txt):
    t = dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext(txt)
    return t


PluginLanguageDomain = "CheckPyCode"
ScreenWidth = 1280 if getDesktop(0).size().width() < 1920 else 1920
getFullPath = lambda fname: resolveFilename(SCOPE_PLUGINS, path.join('Extensions', PluginLanguageDomain, fname))
Pycodestyle2_skin = ETree.parse(getFullPath('skins/skin.xml')).getroot()
getSkin = lambda skinName: ETree.tostring(Pycodestyle2_skin.find('.//screen[@name="%s"]' % skinName), encoding='utf8', method='xml')
localeInit()
language.addCallback(localeInit)
