#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Static Rendering
================

SR means to provide easy methods for rendering plaintext files with human
readable formatting into static html files, for situations when no
complete/dynamic CMS is necessary.

Command line arguments
----------------------
This is the command line handler script. Actual rendering and work takes place
in libsr.py

    - create /path/to/project/directory: 
    create a new project

    - list /path/to/project/directory:
    list all files that have changed in a project

    - render [--force] /path/to/directory:
    render all files that have changed in a project.
    When passing --force, render all files, changed or no

"""


from __future__ import with_statement
import os
import sys
from ConfigParser import SafeConfigParser

from libsr import Project

def create(directory):
    """
    create a new directory and the subdirectories needed for usage with sr
    
    @param directory: path where to create a new project
    @type directory: string
    """
    os.makedirs(directory)
    os.makedirs(os.path.join(directory, 'source'))
    os.makedirs(os.path.join(directory, 'templates'))
    os.makedirs(os.path.join(directory, 'output'))
    
    with open(os.path.join(directory, 'config.ini'), 'w') as configfile:
        config = SafeConfigParser()
        config.add_section('markdown')
        config.add_section('general')
        config.add_section('navigation')
        config.set('markdown', 'safe', 'False')
        config.set('markdown', 'addons', ',')
        config.set('general', 'suffix', '.txt')
        config.set('navigation', '1-index', 'index.html')
        config.write(configfile)
    with open(os.path.join(directory, 'templates', 'standard.html'), 'w') \
        as standard_template:
        standard_template.write('<!-- Put your layout here. -->\n$content\n')
    print "Created a new project under %s" % directory

def list_changed(project):
    """
    print all files that need re-rendering in given project

    @param project: project to check for changed files
    @type project: project object from libsr
    """
    print "Files that need re-rendering: "
    for changed_page in project.list_changed()[0]:
        print " " + changed_page.page_name
    print "Files that don't need to be rendered: "
    for unchanged_page in project.list_changed()[1]:
        print " " + unchanged_page.page_name

def main():
    from optparse import OptionParser
    parser = OptionParser()
    usage = """\
     %prog [-f] command directory

    Supported commands:

    create /path/to/project/dir
        creates a new project under given directory
    list /path/to/project/dir
        list all files that have changed since last rendering in given dir
    render --force /path/to/project/dir
        render all files that have changed since last rendering 
        render all files when given the --force parameter
   """
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--force', default=False, action="store_true",
            dest="force", help="Force rendering even if pages haven't changed"
    )
    (options, args) = parser.parse_args()
    try:
        (command, proj_dir) = args
    except ValueError:
        parser.print_usage()
        sys.exit(1)
    if command == "render":
        project = Project(proj_dir)
        result_pages = project.render(force=options.force)
        print "Pages rendered:"
        print "\n".join(result_pages[0]) or "None"
        print "Pages not rendered:" or "None"
        print "\n".join(result_pages[1])
    elif command == "list":
        project = Project(proj_dir)
        list_changed(project)
    elif command == "create":
        create(proj_dir)
    else:
        print "Unknown command"

if __name__ == '__main__':
        main()  
