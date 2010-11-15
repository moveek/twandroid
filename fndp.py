#!/usr/bin/python2

import sys
import os
import re
import shutil
from setuptools import find_packages

#TARGET_DIR = os.path.join(os.getcwd(), 'target')
PYTHON_FOR_ANDROID='com.googlecode.pythonforandroid'
TARGET_DIR = find_install_target()

print "target: %s" % TARGET_DIR

def find_install_target():
    return [ path for path in sys.path if path.find(PYTHON_FOR_ANDROID) != -1 ][0]

def get_dirs(in_dir='.'):
    return [ name for name in os.listdir(in_dir) if os.path.isdir(os.path.join(in_dir, name)) ]

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

def scrap():
    package = find_package(setup, find_packages(exclude=get_exclude_dirs(setup)))

    if package == []:
        print "No modules found in current directory"
        for d in get_dirs():
            os.chdir(d)
            find_package(setup_file)

def copy_package(setup):
    print "cur dir: %s" % os.getcwd()

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
    py_module = module_name.group(1) + ".py" 
    print "py_module: %s" % py_module
    absolute_module_path = get_absolute_path(py_module)
    shutil.copy(absolute_module_path, TARGET_DIR)
    print "copied: %s" % py_module

def copy_modules_and_packages(setup):
    # Check for single modules that need to be installed
    module_name = re.search("py_modules=\['(\w+)'\]", setup)
    if module_name:
        copy_single_module(module_name)
    else:
        copy_package(setup)

def read_setup():
    if os.listdir('.').count('setup.py') != 0:
        return open('setup.py', 'r').read()

def get_absolute_path(path):
    return os.path.join(os.getcwd(), path)

def get_install_target(package):
    return os.path.join(TARGET_DIR, package) 
            
modules = []

def install():
    for d in get_dirs():

        os.chdir(d)
        print "dir: %s" % d
        print "contents: %s" % os.listdir('.')

        # Open setup.py if one exists. If not, skip the directory.
        setup = read_setup()
        if setup:
            copy_modules_and_packages(setup)
        
        os.chdir("../")

        print "search done"
        raw_input()    
    
install()