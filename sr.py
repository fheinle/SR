#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Static rendering for websites
=============================
This script takes a directory of html templates and source files for content,
formatted in markdown syntax and creates html output from it which can then be
uploaded to any given webhoster without the need for running any programm code
there. 

Markdown addons can be used - the script is shipped with an addon for code 
highlighting, preconfigured to use pygments syntax highlighter. 

Requirements
------------
 * any python version that supports jinja and configobj
 * jinja templating
 * configobj

Additionally, markdown 1.5 is required for it's support of addons.
However, as stable Debian and Ubuntu ship 1.4 in their repos, a recent version
of markdown is shipped with this script.

Installation
------------
Just extract the script and the files it comes with. It doesn't have to be
placed on python path.

Usage
-----
This script works from a set of directorie, which is referred to as an
"instance" hereafter.

Creating instances
~~~~~~~~~~~~~~~~~~
Create those by typing
 
 $ ./sr.py createinstance pathname

You will find 3 directories plus one config file config.ini in pathname.
Source files for pages go into pathname/source or any of it's subdirectories
you create. Files that will be rendered need to have a certain filename
extension, which defaults to .txt - you can change this in config.ini though.

Text will be parsed by markdown. Additionally, you can place any metadata you
want to be passed to templates in email-style headers which have to be
separated from text by one blank line. Examples might be page title, meta
keywords or any other information that doesn't go into the main text passage
and won't be parsed by markdown. If set, the script will use any "templatename"
headers value instead of "standard.html".

Listing files
~~~~~~~~~~~~~

 $ ./sr.py list pathname

This will list all files the script considers to render in a given instance
and their md5 hashes

Rendering single files
~~~~~~~~~~~~~~~~~~~~~~

 $ ./sr.py render_page pathname pagename

This will only render the given page in the given instance directory,
regardless of wether it's been changed or not.

Rendering of whole instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 $ ./sr.py render pathname

This will render all source files in the given instance dir that haven't
changed since the last time the script ran. For this purpose, a file seen_db
will be created automatically which stores md5 hashes for every source file.

Todo
----
 * remove files from output that no longer have a source file, i.e. have been
   deleted in the source directory
 * automate uploading to webhosts
 * integrate smartypants without messing up source code 
 * maybe add some additional storage backends - shelves, databases, et al

Copyright
---------
This script is placed under MIT license

Copyright (c) 2007 Florian Heinle <florian-sr@planet-tiax.de>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import configobj
from email import message_from_file
import shelve
import codecs
import md5
from markdown import markdown
import jinja

def _get_config(instancedir):
    """get the config object for an instance
    @param instancedir: path to instance
    @type instancedir: string
    @returns: configuration for given instance
    @rtype: ConfigObj
    """
    configfile = os.path.join(instancedir, 'config.ini')
    config = configobj.ConfigObj(configfile)
    return config

def _get_hash(instancedir, pagename):
    """calculate an md5 hash of given page.
    @param instancedir: path to instance
    @type instancedir: string
    @param pagename: with path relative to sourcedir, without prefix
    @returns: md5 hash for given file
    @rtype: string"""
    config = _get_config(instancedir)
    suffix = config['general']['source_suffix']
    filename = os.path.join(instancedir, 'source', pagename) + suffix
    page =  open(filename, 'r').read()
    page_hash = md5.new(page).hexdigest()
    return page_hash

def _get_filenames(instancedir):
    """retrieve all files with suffix from config file in instancedir
    
    @param instancedir: path to instance
    @type instancedir: string
    @returns: source files inside the instance
    @rtype: generator
    """
    config = _get_config(instancedir)
    sourcedir = os.path.join(instancedir, 'source')
    suffix = config['general']['source_suffix']
    for directory in os.walk(sourcedir):
        for filename in directory[2]:
            if filename.endswith(suffix):
                yield os.path.join(
                                    directory[0].partition('source')[2],
                                    filename)\
                    [0:-1 * len(config['general']['source_suffix'])]\
                    .lstrip('/')
    
def _load_page(instancedir, pagename):
    """opens a page from filesystem and returns it's data and headers
    @param instancedir: path to instance
    @type instancedir: string
    @param pagename: with path relative to sourcedir, without suffix
    @type pagename: string
    @returns: contents of given pagename and headers
    @rtype: email message-ish object (think dictionary)
    """
    config = _get_config(instancedir)
    sourcedir = os.path.join(instancedir, 'source')
    suffix = config['general']['source_suffix']
    filename = os.path.join(sourcedir, pagename) + suffix
    page = message_from_file(codecs.open(filename, 'r', 'utf-8'))
    return page

def _markup_page(instancedir, page):
    """render a page using markdown and smartypants
    @param instancedir: path to instance
    @type instancedir: string
    @param page: object to render
    @type page: email message object
    @return: rendered contents
    @rtype: string"""
    config = _get_config(instancedir)
    contents = page.get_payload()
    with_markup = markdown(
        contents,
        config['markdown']['addons'],
        safe_mode=config['markdown']['safe_mode'],
    )
    return with_markup

def _render_template(instancedir, page):
    """render a page into a jinja template
    @param instancedir: path to instance
    @type instancedir: string
    @param page: object to render
    @type page: email message object
    @returns: rendered html document
    @rtype: string"""
    jinja_env = jinja.Environment(
        loader=jinja.FileSystemLoader(os.path.join(instancedir, 'templates'))
    )
    if "template" in page:
        templatename = page['template']
    else:
        templatename = 'standard.html'
    template = jinja_env.get_template(templatename)
    contents = {'content':_markup_page(instancedir, page)}
    contents.update(page)
    return template.render(contents)

def list_pages(instancedir):
    """print pages in instancedir with hash
    @param instancedir: path to instance
    @type instancedir: string"""
    instancedir, = instancedir
    seen_db = shelve.open(os.path.join(instancedir, 'seen_db'))
    print "Files in instancedir"
    for filename in _get_filenames(instancedir):
        print "\t" + filename,
        if seen_db.has_key(filename):
            if seen_db[filename] == _get_hash(instancedir, filename):
                print "not modified"
            else:
                print "modified"
    seen_db.close()

def render_page(args):
    """render a givein page
    @param instancedir: path to instance
    @type instancedir: string
    @param pagename: name of the page to render
    @param pagename: string"""
    instancedir = args[0]
    pagename  = args[1]
    config = _get_config(instancedir)
    if pagename.endswith(config['general']['source_suffix']):
        pagename = pagename[0:-1 * len(config['general']['source_suffix'])]
    seen_db = shelve.open(os.path.join(instancedir, 'seen_db'))
    file_hash = _get_hash(instancedir, pagename)
    if seen_db.has_key(pagename):
        if file_hash == seen_db[pagename]:
            print pagename + " has not changed"
            return
    page = _load_page(instancedir, pagename)
    target_filename = os.path.join(instancedir, 'output', pagename)  + '.html'
    if not os.path.isdir(os.path.split(target_filename)[0]):
        os.makedirs(os.path.split(target_filename)[0])
    target_file = codecs.open(target_filename, 'w', 'utf-8')
    target_file.write(_render_template(instancedir, page))
    target_file.close()
    seen_db[pagename] = _get_hash(instancedir, pagename)
    print target_filename + " written"
    seen_db.close()

def render_pages(instancedir):
    """render all pages in given instance dir
    @param instancedir: path to instance
    @type instancedir: string"""
    instancedir, = instancedir
    for pagename in _get_filenames(instancedir):
        render_page([instancedir, pagename])

def create_instance(args):
    """creates a new instance and it's required subdirectories"""
    if len(args) != 1:
        print "Usage: createinstance directory"
        print "Only one directory per call allowed"
        sys.exit(127)
    basedir = args[0]
    if not os.path.isdir(basedir):
        os.makedirs(basedir)
    for dirname in ('templates', 'output', 'source'):
        os.mkdir(os.path.join(basedir, dirname))
    config = configobj.ConfigObj()
    config.filename = os.path.join(basedir, 'config.ini')
    config['markdown'] = {
        'addons':['codehilite'],
        'safe_mode':True,
    }
    config['general'] = {
        'source_suffix':'.txt',
    }
    config.write()

def main():
    """handle command line arguments"""
    run_command = {
        'createinstance':create_instance,
        'list':list_pages,
        'render_page':render_page,
        'render':render_pages,
    }
    usage = ['Available commands:']
    for available_command in run_command.keys():
        usage.append("\t" + available_command)
    if __file__ in sys.argv[0]:
        argumente = sys.argv[1:]
    elif "python" in sys.argv[0]:
        argumente = sys.argv[2:]
    try:
        command = argumente.pop(0)
    except IndexError:
        print "\n".join(usage)
    else:
        try:
            run_command[command](argumente)
        except KeyError:
            print "\n".join(usage)

if __name__ == '__main__':
    main()
