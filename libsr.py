#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
libsr
part of sr, static rendering from markdown formatted textfiles

provides project and page-classes for use with frontend sr.py
"""

import os
import codecs
from ConfigParser import SafeConfigParser
import email
import md5
import shelve

import markdown
import templates

class Project(object):
    """
    base project where all pages are stored inside
    """
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)
        self.config = SafeConfigParser()
        configfile = open(os.path.join(directory, 'config.ini'))
        self.config_hash = md5.md5(configfile.read()).hexdigest()
        configfile.seek(0)
        self.config.readfp(configfile)
        self.sourcedir = os.path.join(self.directory, 'source')
        self.pagesuffix = self.config.get('general', 'suffix')
        self.hash_db = shelve.open(
            os.path.join(self.directory, 'hash.db'),
            writeback=True
        )

    @property
    def pages(self):
        """
        return all pages found in the project's sourcedirectory

        output is relative to project's source directory,
        contains all filenames that carry the suffix supplied in conig.ini,
        sans leading slash and filename suffix
       """
        
        for directory in os.walk(self.sourcedir):
            for filename in directory[2]: 
                if filename.endswith(self.pagesuffix):
                    pagename = os.path.join(
                        directory[0].partition('source')[2],
                        filename
                    )\
                    [0:-1 * len(self.pagesuffix)]\
                    .lstrip('/')
                    yield Page(self, pagename)
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
        list all pages that require rendering

        returns a tuple of ([changed_pages], [unchanged_pages])
        """
        changed_pages = []
        unchanged_pages = []
        if self.config_changed:
            return ([page for page in self.pages],[])
        else:
            for page in self.pages:
                if page.has_changed:
                    changed_pages.append(page.pagename) 
                else:
                    unchanged_pages.append(page.pagename)
            return (changed_pages, unchanged_pages)

    def render(self, force=False):
        """
        render the project

        if not given the argument `force`, render only changed pages
        also render everything when configuration changes
        returns a tuple ([rendered_pages], [unrendered_pages])
        """
        if self.config_changed:
            force = True
            self.hash_db['__config__'] = self.config_hash
            self.hash_db.sync()
        rendered_pages = []
        unrendered_pages = []
        for page in self.pages:
            if page.has_changed or force:
                rendered_pages.append(page.pagename)
                page.render()
            else:
                unrendered_pages.append(page.pagename)
        return (rendered_pages, unrendered_pages)

class Page(object):
    """
    a single page
    """
    def __init__(self, parent_project, pagename):
        """
        set up a page with both it's parent project name and it's own
        """
        self.project = parent_project
        self.pagename = pagename
        pagefile = codecs.open(
            os.path.join(self.project.sourcedir, pagename) + self.project.pagesuffix,
            'r',
            'utf-8',
        )
        self.page = email.message_from_string(pagefile.read().encode('utf-8'))
        if self.page.has_key('template'):
            self.templatename = self.page['template']
        else:
            self.templatename = "standard.html"

    def __repr__(self):
        return "<Page: %s>" % self.pagename

    def markup(self):
        """
        render a page using markdown
        """
        if self.project.config.get('markdown', 'safe').lower() in [
                                                               "true",
                                                               "yes",
                                                               "on"]:
            safe_mode = True
        else:
            safe_mode = False
        return markdown.markdown(self.page.get_payload().decode('utf-8'),
              self.project.config.get('markdown', 'addons').split(',') or None,
              safe_mode,
        )

    def _render_template(self):
        """
        render page's contents into a template

        if the pages has an attribute "temlate" in it's header, it will be used
        instead of the default "standard.html" template.
        """
        template = templates.Template.from_file(
            os.path.join(self.project.directory, 'templates', self.templatename)
            )
        contents = {
            'content':self.markup(),
            'nav':self.project.config.items('navigation'),
        }
        # add additional headers from the source into template context
        contents.update(self.page)
        return template.render(contents)

    @property
    def has_changed(self):
        """
        check if contents of the page have changed or the page is all new
        """
        if not self.project.hash_db.has_key(self.pagename):
            return True
        page_hash = md5.md5(self.page.as_string()).hexdigest()
        if self.project.hash_db[self.pagename] == page_hash:
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
            self.pagename + '.html'
        )
        target_dir = os.path.dirname(target_filename)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        output_file = codecs.open(
            target_filename,
            'w',
            'utf-8',
        )
        new_page_hash = md5.md5(self.page.as_string()).hexdigest()
        self.project.hash_db[self.pagename] = new_page_hash
        self.project.hash_db.sync()
        output_file.write(self._render_template())
        output_file.close()

