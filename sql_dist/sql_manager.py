#!/usr/bin/python

import os
import sys
import re
import argparse
from cStringIO import StringIO
from subprocess import check_output
import pydoc
import shutil

EXTVERSION = check_output('git tag | sort | tail -n 1 | sed -e "s/v//"', shell=True).strip()
EXTVERSION_OLD = check_output('git tag | sort | tail -n 2 | head -n 1 | sed -e "s/v//"', shell=True).strip()
DB_NAME = None
DB_NAME_OLD = None
install_filename = None

def db_name_set(args):
    global DB_NAME, DB_NAME_OLD
    DB_NAME =  ('pgi_test_'+args.project+'_'+EXTVERSION).replace('-','_').replace('.','_')
    DB_NAME_OLD = ('pgi_test_'+args.project+'_'+EXTVERSION_OLD).replace('-','_').replace('.','_')

def get_sql_files(directory):
    directory = os.path.join(directory, 'sql')
    sql_files = []
    for root, dirs, files in os.walk(directory):
        if 'tmp' in dirs:
            dirs.remove('tmp')
        for file in files:
            if file.endswith('.sql'):
                sql_files.append(os.path.join(root, file))

    return sql_files

def load_install_file(filename):
    files = []
    try:
        f = open(filename)
        for line in f:
            x = re.match(r'^\\ir (.*)$', line)
            if x:
                files.append(x.group(1))
        f.close()

        return files
    except IOError, e:
        return None


def compare_install_and_sql_dir(args):
    global install_filename
    install_filename = os.path.join(args.dir,'sql_dist','install.sql')

    f1 = set(get_sql_files(args.dir))
    f2 = load_install_file(install_filename)
    
    if f2 is None:
        print 'install.sql file not found, creating new one (need fix order in this file!!!)'
        f=open(install_filename,'w')
        sf=list(f1)
        sf.sort()
        for fn in sf:
            print >> f, '\ir',fn
        f.close()
        return
    else:
        f2 = set(f2)

    d1 = f1-f2
    d2 = f2-f1

    f=None
    if len(d1)>0:
        print "need add files to install.sql:"
        for fn in d1:
            print '\ir',fn
        if args.force:
            f=open(install_filename,'a')
            print >>f, '\n'
            for fn in d1:
                print >> f, '\ir',fn
            f.close()
            print '\nadded automatically at end of file with force option'

    if len(d2)>0:
        if not args.force:
            print "need remove files from install.sql:"
            for fn in d2:
                print '\ir',fn
        else:
            f=open(install_filename,'r')
            s=StringIO()
            for line in f:
                if not line.replace('\ir ','').strip() in d2:
                    s.write(line)
            f.close()
            f=open(install_filename,'w')
            f.write(s.getvalue())
            f.close()
            s.close()
    if not args.force and (len(d1)>0 or len(d2)>0):
        sys.exit(1)

def build_sql(args):
    global EXTVERSION

    if not EXTVERSION:
        print >>sys.stderr, 'can\'t get project version'
        sys.exit(1)

    if not args.project:
        print >>sys.stderr, 'can\'t get project name'
        sys.exit(1)
    ext_fn=args.project+'--'+EXTVERSION+'.sql'
    print 'creating '+ext_fn
    f=open(ext_fn,'w')
    for fn in load_install_file(install_filename):
        f.write(open(fn).read())
    f.close()

def build(args):
    compare_install_and_sql_dir(args)
    build_sql(args)

def test_load(args):
    global DB_NAME, EXTVERSION
    
    db_name_set(args)
    try:
        print check_output("echo 'DROP DATABASE IF EXISTS %s; CREATE DATABASE %s;' | psql -X -e -h %s postgres" % (DB_NAME, DB_NAME, args.host), shell=True)
        if os.path.exists('tests/test_init_db.sql'):
            print check_output("psql %s -h %s -d %s -f tests/test_init_db.sql" % (args.options, args.host, DB_NAME), shell=True) 
        print check_output("psql %s -h %s -d %s -f %s--%s.sql" % (args.options, args.host, DB_NAME, args.project, EXTVERSION), shell=True)
    except Exception, e:
        sys.exit(1)

def upgrade(args):
    pwd = os.path.join(args.dir,'sql')
    command = 'git diff %s %s %s | colordiff' % (EXTVERSION_OLD, EXTVERSION, pwd)
    print '\n',command +' | less -R\n'   
    pydoc.pipepager(check_output(command, shell = True), cmd = 'less -R')

    try:
        os.mkdir('upgrades')
    except OSError, e:
        pass

    fn=os.path.join('upgrades','%s--%s--%s.sql' % (args.project, EXTVERSION_OLD, EXTVERSION))
    f=open(fn,'w')

    schema = StringIO()
    extensions = StringIO()
    types = StringIO()
    tables = StringIO()
    functions = StringIO()
    triggers = StringIO()
    views = StringIO()
    grants = StringIO()

    command = 'git diff %s %s --name-only %s' % (EXTVERSION_OLD, EXTVERSION, pwd)
    print command,'\n'

    for line in check_output(command, shell = True).split('\n'):
        if line.startswith('sql/schema/'):
            schema.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/extensions/'):
            extensions.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/types/'):
            types.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/tables/'):
            tables.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/functions/'):
            functions.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/triggers/'):
            triggers.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/views/'):
            views.write(open(os.path.join(args.dir,line)).read())
        elif line.startswith('sql/grants/'):
            grants.write(open(os.path.join(args.dir,line)).read())
        print line
    for si in [schema, extensions, types, tables, functions, triggers, views, grants]:
        f.write(si.getvalue())
        si.close()
    f.close()

def test_upgrade(args):
    global DB_NAME, DB_NAME_OLD, EXTVERSION, EXTVERSION_OLD

    db_name_set(args)
    try:
        cleandb(args)
        print check_output("echo 'CREATE DATABASE %s; CREATE DATABASE %s;' | psql -X -e -h %s postgres" % (DB_NAME, DB_NAME_OLD, args.host), shell=True)

        print "load actual version to database"
        command = "psql %s -h %s -d %s -f tests/test_init_db.sql" % (args.options, args.host, DB_NAME)
        print command
        print check_output(command, shell=True)

        command = "psql %s -h %s -d %s -f %s--%s.sql" % (args.options, args.host, DB_NAME, args.project, EXTVERSION)
        print command
        print check_output(command, shell=True)

        print "load old version + upgrade to database"
        command = "psql %s -h %s -d %s -f tests/test_init_db.sql" % (args.options, args.host, DB_NAME_OLD)
        print command
        print check_output(command, shell=True)
        
        command = "psql %s -h %s -d %s -f %s--%s.sql" % (args.options, args.host, DB_NAME_OLD, args.project, EXTVERSION_OLD)
        print command
        print check_output(command, shell=True)
        
        command = "psql %s -h %s -d %s -f upgrades/%s--%s--%s.sql" % (args.options, args.host, DB_NAME_OLD, args.project, EXTVERSION_OLD, EXTVERSION)
        print command
        print check_output(command, shell=True)
        

        print 'extract databases using pg_extractor'
        command = "pg_extractor --host %s --getall --gettriggers -d %s --basedir .pgi_tmp/" % (args.host, DB_NAME)
        print command
        print check_output(command, shell=True)

        command = "pg_extractor --host %s --getall --gettriggers -d %s --basedir .pgi_tmp/" % (args.host, DB_NAME_OLD)
        print command
        print check_output(command, shell=True)


        command = 'diff -r .pgi_tmp/%s .pgi_tmp/%s | colordiff' % (DB_NAME_OLD, DB_NAME)
        print command+' | less -R'

        res=check_output(command, shell = True)
        if len(res)>0:
            pydoc.pipepager(res, cmd = 'less -R')
        else:
            print '\n\nupgrade test was successful, extracted database outputs are same'

    except Exception, e:
        sys.exit(1)

def clean(args):
    global EXTVERSION
    try:
        os.remove(args.project+'--'+EXTVERSION+'.sql')
    except OSError, e:
        pass
    
    try:
        shutil.rmtree('.pgi_tmp')
    except OSError, e:
        pass

def cleandb(args):
    global DB_NAME, DB_NAME_OLD

    db_name_set(args)
    print check_output("echo 'DROP DATABASE IF EXISTS %s; DROP DATABASE IF EXISTS %s;' | psql -X -e -h %s postgres" % (DB_NAME, DB_NAME_OLD, args.host), shell=True)
        
def make_dirs(args):
    for d in ['schema', 'extensions', 'types', 'tables', 'functions', 'triggers', 'views', 'grants']:
        try:
            os.makedirs(os.path.join(args.dir,'sql', d))
        except OSError, e:
            print e

def parse_args():
    parser = argparse.ArgumentParser(description='SQL projects manager')
    parser.add_argument('-p','--project', dest='project', help='project name')
    parser.add_argument('-d','--dir', dest='dir', help='SQL project directory')
    parser.add_argument('-a','--action', dest='action', help='action - (build|test|upgrade|test_upgrade|make_dirs|clean|cleandb)')
    parser.add_argument('--host', dest='host', help='sql devel host for test load and upgrade')
    parser.add_argument('--force', dest='force', action='store_true', help='force update install.sql file')
    parser.add_argument('-o','--options', dest='options', default='-q -1 -X --set ON_ERROR_STOP=1', help='options for psql')
    
    
    args = parser.parse_args()

    # print os.getcwd()
    # print args.dir
    # print args.action

    if args.action == 'build':
        build(args)
    elif args.action == 'test':
        test_load(args)
    elif args.action == 'upgrade':
        upgrade(args)
    elif args.action == 'test_upgrade':
        test_upgrade(args)
    elif args.action == 'clean':
        clean(args)
    elif args.action == 'cleandb':
        cleandb(args)
    elif args.action == 'make_dirs':
        make_dirs(args)
    else:
        print >>sys.stderr, 'wrong action'


if __name__ == '__main__':
    parse_args()
