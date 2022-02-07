#!/usr/bin/env python3

import os, json, pygit2, shutil, re, copy

gitObjects     = []

def init( database ):
    gitWatchObject = json.loads( os.getenv( 'WATCH_GIT_REPOS' ) )
    for gwo in gitWatchObject:
        gitObjects.append( Git( gwo[ 'repo_url' ], gwo[ 'watch' ], database ) )

def watch( database, pushover ):

    if len( gitObjects ) == 0:
        init( database )

    for go in gitObjects:
        go.fetch()

        if go.watch[ 'watch' ] == 'commits':
            newCommits = go.fetchNewCommits()
            go.doWatch( newCommits, pushover )

        if go.watch[ 'watch' ] == 'tags':
            newTags = go.fetchNewTags()
            go.doWatch( newTags, pushover )


class Git:

    basePath = 'temp/{ident}'
    dbTable  = 'git_repos'

    watch    = None
    path     = None
    db       = None
    ident    = None
    repo     = None

    defMsg   = {}

    def __init__( self, repo_url, watch, database ):
        self.db  = database
        self.url = repo_url
        sql = 'SELECT id FROM {dbTable} WHERE url = ?;'.format( dbTable=self.dbTable )
        self.db.startAction()
        self.db.execute( sql, [ repo_url ] )
        try:
            self.ident = self.db.fetchoneNamed()[ 'id' ]
        except:
            sql = 'INSERT INTO {dbTable} ( url ) VALUES ( ? );'.format( dbTable=self.dbTable )
            self.db.execute( sql, [ repo_url ] )
            self.ident = self.db.lastrowid()
        self.db.commitAction()
        self.ident = '{:04}'.format( self.ident )
        self.path  = self.basePath.format( ident=self.ident )
        self.repo  = pygit2.clone_repository( self.url, self.path, bare=True, remote=self.init_remote )
        self.watch = watch

    def __del__( self ):
        """magic function to clean up local repository directories"""
        if self.path != None:
            shutil.rmtree( self.path )

    def doWatch( self, objects, po ):

        if len( objects ) == 0:
            return

        if len( self.defMsg ) == 0:
            attr = [ 'priority', 'title', 'message', 'url', 'url_title', ]
            for a in attr:
                # fetch info
                if a in self.watch:
                    self.defMsg[ a ] = str( self.watch[ a ] )
                elif a in objects[ 0 ].defaults:
                    self.defMsg[ a ] = str( objects[ 0 ].defaults[ a ] )
                else:
                    self.defMsg[ a ] = None
            # priority defaults to 0
            if self.defMsg[ 'priority' ] == None:
                self.defMsg[ 'priority' ] = 0

        phRegEx = r"\{(.*?)\}"
        for o in objects:

            values = {}
            for k in self.defMsg.keys():
                msg    = copy.copy( self.defMsg )
                if k != 'priority':
                    matches = re.finditer( phRegEx, str( msg[ k ] ), re.MULTILINE )
                    for match in matches:
                        for groupNum in range( 0, len( match.groups() ) ):
                            v = match.group( groupNum + 1 )
                            if v not in values:
                                values[ v ] = getattr( o, v )()

            for k in msg:
                if msg[ k ] != None:
                    msg[ k ] = str( msg[ k ] ).format( **values )

            po.messageAll(
                message   = msg[ 'message' ],
                title     = msg[ 'title' ],
                priority  = msg[ 'priority' ],
                url       = msg[ 'url' ],
                url_title = msg[ 'url_title' ]
            )

    def init_remote( self, repo, name, url ):
        # Create the remote with a mirroring url
        remote = repo.remotes.create(name, url, "+refs/*:refs/*")
        # And set the configuration option to true for the push command
        mirror_var = "remote.{}.mirror".format(name.decode())
        repo.config[mirror_var] = True
        # Return the remote, which pygit2 will use to perform the clone
        return remote

    def fetch( self ):
        for remote in self.repo.remotes:
            remote.fetch()

    def fetchNewCommits( self ):
        newCommits = []
        for commit in self.repo.walk( self.repo.head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE ):
            c = Commit( self.ident, str( commit.id ), commit.message.strip(), self.db )
            if c.new():
                newCommits.append( c )
        return newCommits

    def fetchNewTags( self ):
        tags = [ m.group(1) for r in self.repo.references if ( m := re.match( r'^refs/tags/(.+)$', r )) ]
        newTags = []
        for tag in tags:
            t = Tag( self.ident, tag, self.db )
            if t.new():
                newTags.append( t )
        return newTags


class Tag:

    dbTable = 'git_tags'
    isNew   = True
    db      = None
    ident   = None
    name    = None

    defaults = {
        'priority': 0,
        'message': 'There is a new tag ({tag}) published.',
    }

    def __init__( self, repo_id, tag_name, db ):
        self.name = tag_name
        self.db   = db
        sql = 'SELECT id FROM {dbTable} WHERE repo_id = ? AND name = ?;'.format( dbTable=self.dbTable )
        self.db.startAction()
        self.db.execute( sql, [ repo_id, tag_name ] )
        try:
            self.ident = self.db.fetchoneNamed()[ 'id' ]
            self.isNew = False
        except:
            sql = 'INSERT INTO {dbTable} ( repo_id, name ) VALUES ( ?, ? );'.format( dbTable=self.dbTable )
            self.db.execute( sql, [ repo_id, tag_name ] )
            self.ident = self.db.lastrowid()
        self.db.commitAction()

    def new( self ):
        return self.isNew

    def tag( self ):
        return self.name


class Commit:

    dbTable = 'git_commit'
    isNew   = True
    db      = None
    ident   = None
    cid     = None
    message = None

    defaults = {
        'priority': 0,
        'title': 'There is a new commit ({commit}) published!',
        'message': 'Commit-Message for commit ({commit_id}):\n\n===\n\n{commit_message}',
    }

    def __init__( self, repo_id, ident, message, db ):
        self.cid     = ident
        self.db      = db
        self.message = message
        sql = 'SELECT id FROM {dbTable} WHERE repo_id = ? AND ident = ?;'.format( dbTable=self.dbTable )
        self.db.startAction()
        self.db.execute( sql, [ repo_id, ident ] )
        try:
            self.ident = self.db.fetchoneNamed()[ 'id' ]
            self.isNew = False
        except:
            sql = 'INSERT INTO {dbTable} ( repo_id, ident, message ) VALUES ( ?, ?, ? );'.format( dbTable=self.dbTable )
            self.db.execute( sql, [ repo_id, ident, message ] )
            self.ident = self.db.lastrowid()
        self.db.commitAction()

    def new( self ):
        return self.isNew

    def commit( self ):
        return self.cid[0:8]

    def commit_id( self ):
        return self.cid

    def commit_message( self ):
        return self.message
