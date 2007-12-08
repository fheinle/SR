#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
rewrite of sr
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
        """
        if self.config_changed:
            print "Config changed, rendering forced"
            force = True
            self.hash_db['__config__'] = self.config_hash
            self.hash_db.sync()
        for page in self.pages:
            if page.has_changed or force:
                print "Rendering %s" % page.pagename
                page.render()
            else:
                print "Not rendering %s" % page.pagename

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

def create(directory):
    """
    create a new directory and the subdirectories needed for usage with sr
    """
    os.makedirs(directory)
    os.makedirs(os.path.join(directory, 'source'))
    os.makedirs(os.path.join(directory, 'templates'))
    os.makedirs(os.path.join(directory, 'output'))
    configfile = open(os.path.join(directory, 'config.ini'), 'w')
    config = SafeConfigParser()
    config.add_section('markdown')
    config.add_section('general')
    config.add_section('navigation')
    config.set('markdown', 'safe', 'False')
    config.set('markdown', 'addons', 'codehilite,')
    config.set('general', 'suffix', '.txt')
    config.set('navigation', 'index', 'index.html')
    config.write(configfile)

def list_changed(project):
    """
    print all files that need re-rendering in given project
    """
    print "Files that need re-rendering: "
    for changed_page in project.list_changed()[0]:
        print " " + changed_page.pagename
    print "Files that don't need to be rendered: "
    for unchanged_page in project.list_changed()[1]:
        print " " + unchanged_page.pagename

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    usage = "usage: %prog [-f] command directory"
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--force', default=False, action="store_true",
            dest="force", help="Force rendering even if pages haven't changed"
    )
    (options, args) = parser.parse_args()
    (command, proj_dir) = args
    if command == "render":
        project = Project(proj_dir)
        project.render(force=options.force)
    elif command == "list":
        project = Project(proj_dir)
        list_changed(project)
    elif command == "create":
        create(proj_dir)
    else:
        print "Unknown command"
