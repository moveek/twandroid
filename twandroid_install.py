#!/usr/bin/python2
"""
    twandroid_install.py

    Provides a function to install python packages 
    and modules under the Scripting Layer for Android (SL4A). 

    This script makes use of two functions: find_packages() and 
    convert_path() lifted directly from setuptools and 
    distutils.util respectively.

"""
import sys
import os
import re
import shutil

# Location of extra python libraries. Additional
# packages should be installed here.
PYTHON_FOR_ANDROID='com.googlecode.pythonforandroid'
TARGET_DIR = find_install_target()
#TARGET_DIR = os.path.join(os.getcwd(), 'target')

print "target: %s" % TARGET_DIR

def find_install_target():
    """Check sys.path to find out where python_extras are installed"""
    return [ path for path in sys.path if path.find(PYTHON_FOR_ANDROID) != -1 ][0]

# Lifted from setuptools
def find_packages(where='.', exclude=()):
    """Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).
    """
    out = []
    stack=[(convert_path(where), '')]
    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if ('.' not in name and os.path.isdir(fn) and
                os.path.isfile(os.path.join(fn,'__init__.py'))
            ):
                out.append(prefix+name); stack.append((fn,prefix+name+'.'))
    for pat in list(exclude)+['ez_setup', 'distribute_setup']:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item,pat)]
    return out

# Lifted from distutils.util--required by find_packages()
def convert_path (pathname):
    """Return 'pathname' as a name that will work on the native filesystem,
    i.e. split it on '/' and put it back together again using the current
    directory separator.  Needed because filenames in the setup script are
    always supplied in Unix style, and have to be converted to the local
    convention before we can actually use them in the filesystem.  Raises
    ValueError on non-Unix-ish systems if 'pathname' either starts or
    ends with a slash.
    """
    if os.sep == '/':
        return pathname
    if not pathname:
        return pathname
    if pathname[0] == '/':
        raise ValueError, "path '%s' cannot be absolute" % pathname
    if pathname[-1] == '/':
        raise ValueError, "path '%s' cannot end with '/'" % pathname

    paths = string.split(pathname, '/')
    while '.' in paths:
        paths.remove('.')
    if not paths:
        return os.curdir
    return os.path.join(*paths)

def get_exclude_dirs(setup_file):
    """ 
    Check setup.py to see if any modules should be excluded
    from the installed package.
    """
    if setup_file == []:
        return

    exclude = []
    try:
        found = re.search("find_packages.*\)", setup_file)
        exclude = re.split('[^A-Za-z0-9_.*]+', re.search("exclude(.*)\)", found.group(0)).group(1))
        print "exclude: %s" % exclude
    except AttributeError:
        print "No dirs to exlude."
    return exclude

def copy_into(src, dst):
    """
    Copy src file or directory into dst.
    """
    for f in os.listdir(src):
        copy_from = os.path.join(src,f)
        copy_to = os.path.join(dst, f)
        if os.path.isdir(copy_from):
            shutil.copytree(copy_from, copy_to)
        else:
            shutil.copy(copy_from, copy_to)

def find_package(setup, found_package):
    """
    Starting from current directory, recursively
    traverse sub directories till find_packages() finds
    packages.
    """
    if found_package:
        print "found_package: %s" % found_package 
        return get_absolute_path(found_package[0])
    else:
        package = []
        for d in get_dirs():
            os.chdir(d)
            package = find_package(setup, find_packages(exclude=get_exclude_dirs(setup)))
            os.chdir("../")

        return package

def copy_package(setup):
    """
    Find and copy the package files to the install target.
    If modules of the same package exist across multiple directories
    in the same namespace, all the files are installed into the same package directory
    in the install target.

    e.g. If package mypkg has module1 and module2 in separate directories:
            src/
              mypkg.module1/
                mypkg/
                  module1
                  ..
              mypkg.module2/
                mypkg/
                  module2
                  ..
              ..
         The modules will be copied into the same package directory at the target:
            mypkg/ 
              module1
              module2
              ..
    """
    top_level_package = find_package(setup, find_packages(exclude=get_exclude_dirs(setup)))
    print "package is: %s" % top_level_package
    try:
        install_target = get_install_target(os.path.basename(top_level_package))
        print "install_target: %s" % install_target
        os.stat(install_target)

        # If we get here, the install_target already exists. This means
        # The package is already partly installed and we need to copy 
        # modules into it.
        copy_into(top_level_package, install_target)

    except OSError:
        # Target doesn't exist yet, so install the package.
        shutil.copytree(top_level_package, install_target)
        
def copy_single_module(module_name):
    """
    Copy a single module to the install target.
    """
    py_module = module_name.group(1) + ".py" 
    absolute_module_path = get_absolute_path(py_module)
    shutil.copy(absolute_module_path, TARGET_DIR)
    print "copied: %s" % py_module

def copy_modules_and_packages(setup):
    """
    Copy both packages and individual modules to the target
    """
    # Check setup.py for single modules that need to be installed
    module_name = re.search("py_modules=\['(\w+)'\]", setup)
    if module_name:
        copy_single_module(module_name)
    else:
        copy_package(setup)

def read_setup():
    """
    Read setup.py. Later used to find out about the package structure.
    """
    if os.listdir('.').count('setup.py') != 0:
        return open('setup.py', 'r').read()

def get_dirs(in_dir='.'):
    return [ name for name in os.listdir(in_dir) if os.path.isdir(os.path.join(in_dir, name)) ]

def get_absolute_path(path):
    return os.path.join(os.getcwd(), path)

def get_install_target(package):
    return os.path.join(TARGET_DIR, package) 
            
def install():
    for d in get_dirs():

        os.chdir(d)
        print "dir: %s" % d
        print "contents: %s" % os.listdir('.')

        setup = read_setup()
        if setup:
            copy_modules_and_packages(setup)
            print "package installed"
        else:
            print "not a python package: skipping..."
            
        
        os.chdir("../")

        raw_input()    
    
install()
