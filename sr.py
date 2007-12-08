#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
sr
part of sr, static rendering from markdown formatted textfiles

provides a frontend to libsr
"""

import os
from ConfigParser import SafeConfigParser

from libsr import Project

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
        print " " + changed_page
    print "Files that don't need to be rendered: "
    for unchanged_page in project.list_changed()[1]:
        print " " + unchanged_page

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
