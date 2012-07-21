==================
django-feedstorage
==================

This is an application designed for storing Feeds entries 
and notifying subscribers only when there are new entries.

It has 2 dependencies: ``requests`` and ``lxml``.

For now, it has just been tested with: Python 2.7, Django 1.4, requests 0.13.2 and lxml 2.3.4
but feel free to try it with other versions and let me know.

For installation instructions, see the file "INSTALL" in this
directory; for instructions on how to use this application, and on
what it provides, see the file "overview.rst" in the "docs/"
directory.


  
  
Next things to do
-------------------

* write tests
* write more documentation
* test with older versions of python and django
* add Scheduling in the admin
* handle more feed formats
* notify new entries in a merged XML file instead of several Entry objects
* refactoring: create a "callback" custom field to serialize/deserialize a callable object
