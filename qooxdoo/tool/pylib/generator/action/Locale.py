#!/usr/bin/env python

################################################################################
#
#  qooxdoo - the new era of web development
#
#  http://qooxdoo.org
#
#  Copyright:
#    2006-2009 1&1 Internet AG, Germany, http://www.1und1.de
#
#  License:
#    LGPL: http://www.gnu.org/licenses/lgpl.html
#    EPL: http://www.eclipse.org/org/documents/epl-v10.php
#    See the LICENSE file in the project's top-level directory for details.
#
#  Authors:
#    * Sebastian Werner (wpbasti)
#
################################################################################

import os, sys, re
import time, datetime

from polib import polib
from ecmascript.frontend import treeutil, tree
from misc import cldr, util, filetool, util
from generator.code.LibraryPath import LibraryPath

class Locale:
    def __init__(self, context, classes, translation, cache, console, treeLoader):
        self._context = context
        self._classes = classes
        self._translation = translation
        self._cache = cache
        self._console = console
        self._treeLoader = treeLoader



    def getLocalizationData(self, targetLocales):
        self._console.debug("Generating localization data...")
        self._console.indent()

        data = {}
        root = os.path.join(filetool.root(), os.pardir, "data", "cldr", "main")

        newlocales = targetLocales
        for locale in targetLocales:
            if len(locale) > 2 and locale[2] == "_":
              topLevelLocale = locale[0:2]
              if not topLevelLocale in targetLocales:
                self._console.warn("Base locale %s not specified, trying to add it." % topLevelLocale)
                newlocales[:0] = [topLevelLocale]

        for entry in newlocales:
            if entry == "C":
                locale = "en"
            else:
                locale = entry
            locFile = os.path.join(root, "%s.xml" % locale)
            cacheId = "locale-%s-%s" % (root, locale)

            locDat = self._cache.read(cacheId, locFile)
            if locDat == None:
                self._console.debug("Processing locale: %s" % locale)
                locDat = cldr.parseCldrFile(locFile)
                self._cache.write(cacheId, locDat)

            data[entry] = locDat

        self._console.outdent()
        return data



    def getTranslationDataX(self, targetLocales, namespace):
        self._console.debug("Generating translation data for namespace %s..." % namespace)
        self._console.indent()

        data = []
        for entry in targetLocales:
            self._console.debug("Processing locale: %s" % entry)
            # TODO

        self._console.outdent()
        return "".join(data)



    def getPotFile(self, content, variants=None):
        pot = self.createPoFile()
        strings = self.getPackageStrings(content, variants)

        for msgid in strings:
            # create poentry
            obj = polib.POEntry(msgid=msgid)
            pot.append(obj)

            # convert to polib style
            if self._context["jobconf"].get("translate/poentry-with-occurrences", True):
                obj.occurrences = []
                for location in strings[msgid]["occurrences"]:
                    obj.occurrences.append((re.sub(r'\\', "/", location["file"]), location["line"]))

            # adding a hint/comment if available
            if "hint" in strings[msgid]:
                obj.comment = strings[msgid]["hint"]
            
            if "plural" in strings[msgid]:
                obj.msgid_plural = strings[msgid]["plural"]
                obj.msgstr_plural[u'0'] = ""
                obj.msgstr_plural[u'1'] = ""

        pot.sort()

        return pot



    def updateTranslations(self, namespace, translationDir, localesList=None):

        def parsePOEntryStrings(poset):
            for poentry in poset:
                poentry.msgid        = self.parseAsUnicodeString(poentry.msgid)
                poentry.msgid_plural = self.parseAsUnicodeString(poentry.msgid_plural)
                if poentry.msgstr_plural:
                    for pos in poentry.msgstr_plural:
                        poentry.msgstr_plural[pos] = self.parseAsUnicodeString(poentry.msgstr_plural[pos])

        def unescapeMsgIds(poset):
            for poentry in poset:
                if poentry.msgid.find(r'\\') > -1:
                    poentry.msgid = self.recoverBackslashEscapes(poentry.msgid)

        self._console.info("Updating namespace: %s" % namespace)
        self._console.indent()
        
        self._console.debug("Looking up relevant class files...")
        classList = []
        classes = self._classes
        for classId in classes:
            if classes[classId]["namespace"] == namespace:
                classList.append(classId)
                    
        self._console.debug("Compiling filter...")
        pot = self.getPotFile(classList)
        pot.sort()

        allLocales = self._translation[namespace]
        if localesList == None:
            selectedLocales = allLocales.keys()
        else:
            selectedLocales = localesList
            for locale in selectedLocales:
                if locale not in allLocales:
                    path = os.path.join(translationDir, locale + ".po")
                    f    = open(path, 'w')  # create stanza file
                    pof  = self.createPoFile()
                    f.write(str(pof))
                    f.close()
                    allLocales[locale] = LibraryPath.translationEntry(locale, path, namespace)

        self._console.info("Updating %d translations..." % len(selectedLocales))
        self._console.indent()

        for locale in selectedLocales:
            self._console.debug("Processing: %s" % locale)

            entry = allLocales[locale]
            po = polib.pofile(entry["path"])
            po.merge(pot)
            po.sort()
            #po.save(entry["path"])
            poString = str(po)
            #poString = self.recoverBackslashEscapes(poString)
            filetool.save(entry["path"], poString)

        self._console.outdent()
        self._console.outdent()



    def recoverBackslashEscapes(self, s):
        # collapse \\ to \
        return s.replace(r'\\', '\\')

    def getTranslationData(self, classList, variants, targetLocales):
        # Generate POT file to filter PO files
        self._console.debug("Compiling filter...")
        pot = self.getPotFile(classList, variants)

        if len(pot) == 0:
            return {}

        # Find all influenced namespaces
        libnames = {}
        for classId in classList:
            ns = self._classes[classId]["namespace"]
            libnames[ns] = True

        # Create a map of locale => [pofiles]
        PoFiles = {}
        for libname in libnames:
            liblocales = self._translation[libname]  # {"en": <translationEntry>, ...}

            for locale in targetLocales:
                if locale in liblocales:
                    if not locale in PoFiles:
                        PoFiles[locale] = []
                    PoFiles[locale].append(liblocales[locale]["path"]) # collect all .po files for a given locale

        # Load po files
        blocks = {}
        for locale in PoFiles:
            self._console.debug("Processing translation: %s" % locale)
            self._console.indent()

            result = {}
            for path in PoFiles[locale]:
                self._console.debug("Reading file: %s" % path)

                po = polib.pofile(path)
                po.merge(pot)
                translated = po.translated_entries()
                
                result.update(self.entriesToDict(translated))

            self._console.debug("Formatting %s entries" % len(result))
            blocks[locale] = result
            self._console.outdent()

        return blocks


    def getTranslationData_1(self, classList, variants, targetLocales):

        def extractTranslations(pot,po):
            for potentry in pot:
                otherentry = po.find(potentry.msgid)
                if otherentry:
                    potentry.msgstr = otherentry.msgstr
                    #potentry.msgid_plural remains
                    if otherentry.msgstr_plural:
                        for pos in otherentry.msgstr_plural:
                            potentry.msgstr_plural[pos] = otherentry.msgstr_plural[pos]
            return

        # Generate POT file to filter PO files
        self._console.debug("Compiling filter...")
        pot = self.getPotFile(classList, variants)

        if len(pot) == 0:
            return {}

        # Find all influenced namespaces
        libnames = {}
        for classId in classList:
            ns = self._classes[classId]["namespace"]
            libnames[ns] = True

        # Create a map of locale => [pofiles]
        PoFiles = {}
        for libname in libnames:
            liblocales = self._translation[libname]  # {"en": <translationEntry>, ...}

            for locale in targetLocales:
                if locale in liblocales:
                    if not locale in PoFiles:
                        PoFiles[locale] = []
                    PoFiles[locale].append(liblocales[locale]["path"]) # collect all .po files for a given locale

        # Load po files
        blocks = {}
        for locale in PoFiles:
            self._console.debug("Processing translation: %s" % locale)
            self._console.indent()

            result = {}
            for path in PoFiles[locale]:
                self._console.debug("Reading file: %s" % path)

                po = polib.pofile(path)
                extractTranslations(pot,po)

            translated = pot.translated_entries()
            result.update(self.entriesToDict(translated))

            self._console.debug("Formatting %s entries" % len(result))
            blocks[locale] = result
            self._console.outdent()

        return blocks





    def entriesToDict(self, entries):
        all = {}

        for entry in entries:
            if ('msgstr_plural' in dir(entry) and
                '0' in entry.msgstr_plural and '1' in entry.msgstr_plural):
                all[entry.msgid]        = entry.msgstr_plural['0']
                all[entry.msgid_plural] = entry.msgstr_plural['1']
                # missing: handling of potential msgstr_plural[2:N]
            else:
                all[entry.msgid] = entry.msgstr

        return all



    def msgfmt(self, data):
        result = []

        for msgid in data:
            result.append('"%s":"%s"' % (msgid, data[msgid]))

        return "{" + ",".join(result) + "}"



    def createPoFile(self):
        po = polib.POFile()
        now = util.nowString()

        po.metadata['Project-Id-Version']   = '1.0'
        po.metadata['Report-Msgid-Bugs-To'] = 'you@your.org'
        po.metadata['POT-Creation-Date']    = now
        po.metadata['PO-Revision-Date']     = now
        po.metadata['Last-Translator']      = 'you <you@your.org>'
        po.metadata['Language-Team']        = 'Team <yourteam@your.org>'
        po.metadata['MIME-Version']         = '1.0'
        po.metadata['Content-Type']         = 'text/plain; charset=utf-8'
        po.metadata['Content-Transfer-Encoding'] = '8bit'

        return po


    def parseAsUnicodeString(self, s):
        n = s
        if n.find('\\') > -1:
            if n.find('"') > -1:
                qmark = "'"
            else:
                qmark = '"'
            #n = eval(repr(s))  # evaluate \escapes; -- doesn't work
            n = eval('u' + qmark + s + qmark)  # evaluate \escapes
        return n


    def getPackageStrings(self, content, variants):
        """ combines data from multiple classes into one map """

        self._console.debug("Collecting package strings...")
        self._console.indent()
        
        result = {}
        for classId in content:
            translation = self.getTranslation(classId, variants)

            for source in translation:
                #msgid = self.parseAsUnicodeString(source["id"])  # parse raw data as string, to translate \escapes
                msgid = source["id"]

                if result.has_key(msgid):
                    target = result[msgid]
                else:
                    target = result[msgid] = {
                        "occurrences" : []
                    }

                    if source.has_key("plural"):
                        target["plural"] = self.parseAsUnicodeString(source["plural"])

                    if source.has_key("hint"):
                        target["hint"] = source["hint"]

                target["occurrences"].append({
                    "file" : self._classes[classId]["relpath"],
                    "line" : source["line"],
                    "column" : source["column"]
                })

        self._console.debug("Package contains %s unique translation strings" % len(result))
        self._console.outdent()
        return result



    def getTranslation(self, fileId, variants):
        fileEntry = self._classes[fileId]
        filePath = fileEntry["path"]

        variantsId = util.toString(variants)

        cacheId = "translation-%s-%s" % (filePath, variantsId)

        translation = self._cache.readmulti(cacheId, filePath)
        if translation != None:
            return translation

        self._console.debug("Looking for translation strings: %s..." % fileId)
        self._console.indent()

        tree = self._treeLoader.getTree(fileId, variants)

        try:
            translation = self._findTranslationBlocks(tree, [])
        except NameError, detail:
            self._console.error("Could not extract translation from %s!" % fileId)
            self._console.error("%s" % detail)
            sys.exit(1)

        if len(translation) > 0:
            self._console.debug("Found %s translation strings" % len(translation))

        self._console.outdent()
        self._cache.writemulti(cacheId, translation)

        return translation



    def _findTranslationBlocks(self, node, translation):
        if node.type == "call":
            oper = node.getChild("operand", False)
            if oper:
                var = oper.getChild("variable", False)
                if var:
                    varname = (treeutil.assembleVariable(var))[0]
                    for entry in [ ".tr", ".trn", ".trc", ".marktr" ]:
                        if varname.endswith(entry):
                            self._addTranslationBlock(entry[1:], translation, node, var)
                            break

        if node.hasChildren():
            for child in node.children:
                self._findTranslationBlocks(child, translation)

        return translation



    def _addTranslationBlock(self, method, data, node, var):
        entry = {
            "method" : method,
            "line" : node.get("line"),
            "column" : node.get("column")
        }

        # tr(msgid, args)
        # trn(msgid, msgid_plural, count, args)
        # trc(hint, msgid, args)
        # marktr(msgid)

        if method == "trn" or method == "trc": no=2
        else: no=1

        params = node.getChild("params", False)
        if not params or not params.hasChildren():
            raise NameError("Invalid param data for localizable string method at line %s!" % node.get("line"))

        strings = []
        for child in params.children:
            if child.type == "commentsBefore":
                continue

            elif child.type == "constant" and child.get("constantType") == "string":
                strings.append(child.get("value"))

            elif child.type == "operation":
                strings.append(self._concatOperation(child))

            elif len(strings) < no:
                raise NameError("Unsupported param of type %s at line %s" % (child.type, child.get("line")))

            # Ignore remaining params (arguments)
            if len(strings) == no:
                break

        if len(strings) != no:
            raise NameError("Invalid number of parameters %s at line %s" % (len(strings), node.get("line")))

        if method == "trc":
            entry["hint"] = strings[0]
            entry["id"] = strings[1]
        else:
            entry["id"] = strings[0]

        if method == "trn":
            entry["plural"] = strings[1]

        data.append(entry)



    def _concatOperation(self, node):
        result = ""

        try:
            first = node.getChild("first").getChildByTypeAndAttribute("constant", "constantType", "string")
            result += first.get("value")

            second = node.getChild("second").getFirstChild(True, True)
            if second.type == "operation":
                result += self._concatOperation(second)
            else:
                result += second.get("value")

        except tree.NodeAccessException:
            raise NameError("Unsupported param of type at line %s" % node.get("line"))

        return result
