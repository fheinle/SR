#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manage directories for static rendering

Usage:
    manage.py action [target]
        
        --create-dir dirname
"""

import os
import sys
import configobj
from email import message_from_file
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
    with_markup = markdown(contents, config['markdown']['addons'])
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
    print "Files in instancedir"
    for filename in _get_filenames(instancedir):
        print "\t%s: %s" % (filename, _get_hash(instancedir, filename))

def render_page(args):
    """render a givein page
    @param instancedir: path to instance
    @type instancedir: string
    @param pagename: name of the page to render
    @param pagename: string"""
    instancedir = args[0]
    pagename  = args[1]
    config = _get_config(instancedir)
    pagename.rstrip(config['general']['source_suffix'])
    page = _load_page(instancedir, pagename)
    target_filename = os.path.join(instancedir, 'output', pagename)  + '.html'
    if not os.path.isdir(os.path.split(target_filename)[0]):
        os.makedirs(os.path.split(target_filename)[0])
    target_file = codecs.open(target_filename, 'w', 'utf-8')
    target_file.write(_render_template(instancedir, page))
    target_file.close()
    print target_filename + " written"

def render_pages(instancedir):
    """render all pages in given instance dir
    @param instancedir
    @type string"""
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
        'render_page':render_page,
        'list':list_pages,
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
