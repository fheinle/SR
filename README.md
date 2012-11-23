# Introduction

Maintaining small websites doesn't always require full-blown content management systems.
Installation is a hassle, dynamic webspace might cost more and there's tons of features you don't need, when all you want to do is deliver some static information that doesn't change by the minute.

## Why SR?

SR allows you to keep a directory on your local harddisk with plain text files that keep your content in a format that is readable by both humans and machines (markdown formatted). That way, you can focus on writing your content and don't bother with HTML formatting options and tags. Completely stripping out HTML noise from your content also makes it easier to keep your content under version control systems.

You still won't lose your freedom as a web artist. SR renders your content into a set of templates you provide. It features an easy to learn mini template language.

# Features

* renders all your .txt files inside a source directory
* won't render what hasn't changed (good for larger projects)
* uses [markdown](http://daringfireball.net/projects/markdown/) for rendering
* supports markdown addons (e.g. [Codehilite](http://achinghead.com/markdown/codehilite/) for syntax highlighting)
* features a small template language, supporting python expressions (taken from the Werkzeug project)

# Downloads

Installation requires Python, Markdown for Python (>= 1.5) and setuptools. The versions shipped with Ubuntu Hardy+ will do.

## tarball

[Download the tarball from github](https://github.com/fheinle/SR/archive/master.zip). Installation is easy, run as root:

    python setup.py install

## Ubuntu Hardy package

Create ``/etc/apt/sources.list.d/sr.list`` with the following two lines:

    deb http://ppa.launchpad.net/tiax/ubuntu hardy main
    deb-src http://ppa.launchpad.net/tiax/ubuntu hardy main

and install the package ``sr``.
