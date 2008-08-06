#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Static Rendering
================

libsr
-----

This is the part of sr that distinguishes directories into projects
"""

import os
import sys
import codecs
import shelve
from ConfigParser import SafeConfigParser
from email import message_from_string
from md5 import md5
sys.path.append(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'MarkdownAddons',
    )
)
from markdown import markdown

import templates

class Project(object):
    """
    base project where all pages are stored inside. MD5Sums of pages are 
    stored in a hash db inside a shelve
    """
    def __init__(self, directory):
        """
        open the config file and hash db

        @param directory: path to the directory the project is olocated in
        @type directory: string
        """

        self.directory = os.path.abspath(directory)
        self.config = SafeConfigParser()
        try:
            config_file = open(os.path.join(directory, 'config.ini'))
        except IOError:
            sys.exit(
                "Error: couldn't open configfile - is %s an sr project?" %
                directory
            )
        self.config_hash = md5(config_file.read()).hexdigest()
        config_file.seek(0)
        self.config.readfp(config_file)
        self.source_dir = os.path.join(self.directory, 'source')
        self.page_suffix = self.config.get('general', 'suffix')
        self.hash_db = shelve.open(
            os.path.join(self.directory, 'hash.db'),
            writeback=True
        )

    @property
    def pages(self):
        """
        find all source files in the project directory
        
        output is relative to project's source directory,
        contains all filenames that carry the suffix supplied in conig.ini,
        sans leading slash and filename suffix
       """
        for directory in os.walk(self.source_dir):
            for filename in directory[2]: 
                if filename.endswith(self.page_suffix):
                    page_name = os.path.join(
                        directory[0].partition('source')[2],
                        filename
                    )\
                    [0:-1 * len(self.page_suffix)]\
                    .lstrip('/')
                    yield Page(self, page_name)

    @property
    def config_changed(self):
        """
        check if configuration file has changed
        """
        if not self.hash_db.has_key('__config__') or not\
            self.config_hash == self.hash_db['__config__']:
            return True

    def list_changed(self):
        """
        list all pages that require rendering because they have changed

        lists all pages, if the config file has changed

        @return: lists of changed and unchanged pages
        @rtype: tuple of lists
        """
        changed_pages = []
        unchanged_pages = []
        if self.config_changed:
            return ([page for page in self.pages], [])
        else:
            for page in self.pages:
                if page.has_changed:
                    changed_pages.append(page.page_name) 
                else:
                    unchanged_pages.append(page.page_name)
            return (changed_pages, unchanged_pages)

    def render(self, force=False):
        """
        render the project

        renders only changed pages or all pages, if config changed 

        @keyword force: if not given, render only pages that have changed
                        since last run. If given, render everything
        @return: lists of rendered and unrendered pages
        @rtype: tuple of lists
        """
        if self.config_changed:
            force = True
            self.hash_db['__config__'] = self.config_hash
            self.hash_db.sync()
        rendered_pages = []
        unrendered_pages = []
        for page in self.pages:
            if page.has_changed or force:
                rendered_pages.append(page.page_name)
                page.render()
            else:
                unrendered_pages.append(page.page_name)
        return (rendered_pages, unrendered_pages)

class Page(object):
    """
    a single page
    """
    def __init__(self, parent_project, page_name):
        """
        set up a page with both it's parent project name and it's own

        @param parent_project: related project
        @type parent_project: Project object
        @param page_name: page filename
        @type page_name: string
        """
        self.project = parent_project
        self.page_name = page_name
        page_file = codecs.open(
            os.path.join(self.project.source_dir, page_name) \
              + self.project.page_suffix,
            'r',
            'utf-8',
        )
        self.page = message_from_string(page_file.read().encode('utf-8'))
        if self.page.has_key('template'):
            self.template_name = self.page['template']
        else:
            self.template_name = "standard.html"

    def __repr__(self):
        return "<Page: %s>" % self.page_name

    def markup(self):
        """
        render a page using markdown
        
        @return: rendered html contents
        """
        if self.project.config.get('markdown', 'safe').lower() in [
                                                               "true",
                                                               "yes",
                                                               "on"]:
            safe_mode = True
        else:
            safe_mode = False
        addons = [addon for addon in 
                self.project.config.get('markdown', 'addons').split(',')
                  if addon]
        return markdown(text=self.page.get_payload().decode('utf-8'),
              safe_mode=safe_mode,
              extensions=addons,
        )

    def _render_template(self):
        """
        render page's contents into a template

        if the pages has an attribute "temlate" in it's header, it will be used
        instead of the default "standard.html" template.

        @return: complete html page
        @rtype: string
        """
        template = templates.Template.from_file(
            os.path.join(
                self.project.directory, 
                'templates',
                self.template_name)
            )
        navigation = [(nav_item[0].split('-',1)[1], nav_item[1]) 
                      for nav_item in 
                    sorted(self.project.config.items('navigation'))]
        contents = {
            'content':self.markup(),
            'nav':navigation,
        }
        # add additional headers from the source into template context
        contents.update(self.page)
        return template.render(contents)

    @property
    def has_changed(self):
        """
        check if contents of the page have changed or the page is all new
        """
        if not self.project.hash_db.has_key(self.page_name):
            return True
        page_hash = md5(self.page.as_string()).hexdigest()
        if self.project.hash_db[self.page_name] == page_hash:
            return False
        else:
            return True

    def render(self):
        """
        render the page into a static html file

        if `force` isn't true, md5 hashes will be compared to find out
        if re-rendering the page is really necessary.
        """
        target_filename = os.path.join(
            self.project.directory,
            'output',
            self.page_name + '.html'
        )
        target_dir = os.path.dirname(target_filename)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        output_file = codecs.open(
            target_filename,
            'w',
            'utf-8',
        )
        new_page_hash = md5(self.page.as_string()).hexdigest()
        self.project.hash_db[self.page_name] = new_page_hash
        self.project.hash_db.sync()
        output_file.write(self._render_template())
        output_file.close()
