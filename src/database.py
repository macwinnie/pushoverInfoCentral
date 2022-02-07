#!/usr/bin/env python3

###
## prepare database
###

import pathlib, sqlite3, yoyo, os

curpath        = str( pathlib.Path().resolve() )
dbfile         = '{}/{}'.format( curpath, os.getenv( 'DBFILE', 'database.sqlite' ) )
migrations_dir = '{}/{}'.format( curpath, 'db_migrations' )
dbback         = 'sqlite:///{}'.format( dbfile )

# ensure DB file exists
if not os.path.isfile( dbfile ):
    open( dbfile, 'w' ).close()

# ensure all DB migrations are applied
backend    = yoyo.get_backend( dbback )
migrations = yoyo.read_migrations( migrations_dir )
backend.apply_migrations( backend.to_apply( migrations ))

class db:

    connection = None
    result     = None

    def __init__( self ):
        pass

    def __getattr__( self, name ):
        # args:   positional arguments
        # kwargs: keyword arguments
        def method( *args, **kwargs ):
            cllbl = getattr( self.result, name )
            if callable( cllbl ):
                return cllbl( *args, **kwargs )
            else:
                return cllbl
        return method

    def startAction( self ):
        if self.connection != None:
            raise Exception( 'DB already connected!' )
        self.connection = sqlite3.connect( dbfile )

    def fullExecute( self, query, params=[] ):
        self.startAction()
        self.execute( query, params )
        self.commitAction()

    def execute( self, query, params=[] ):
        self.result = self.connection.cursor()
        self.result.execute( query, params )

    def close( self ):
        self.connection.close()
        self.connection = None

    def commitAction( self ):
        self.connection.commit()
        self.close()

    def rollbackAction( self ):
        self.connection.rollback()
        self.close()

    def fetchallNamed( self ):
        rowKeys    = [ i[ 0 ] for i in self.description() ]
        allResults = self.fetchall()
        allReturn  = []
        for ar in allResults:
            allReturn.append( dict( zip( rowKeys, ar ) ) )
        return allReturn

    def fetchoneNamed( self ):
        rowKeys  = [ i[ 0 ] for i in self.description() ]
        results  = self.fetchone()
        toReturn = dict( zip( rowKeys, results ) )
        return toReturn
