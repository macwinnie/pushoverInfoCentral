#!/usr/bin/env python3

import requests, os, json, datetime

class device:
    """Pushover Device"""
    name = None

    def __init__( self, name ):
        self.name = name


class user:
    """Pushover User"""
    token   = None
    devices = []

    def __init__( self, token, device=None ):
        self.token = token
        if device != None:
            self.devices.append( device )

    def addDevice( self, name ):
        self.devices.appen( name )


class app:
    """Pushover App"""
    token = None

    def __init__( self, token ):
        self.token = token


class receipt:
    """Pushover receipt handling"""
    receipt = None
    app     = None
    apiUrl  = None
    info    = None

    def __init__( self, receipt, app ):
        self.apiUrl = pushover.baseUrl.format( location='receipts/{receipt}.json?token={app}'.format( receipt=receipt, app=app ) )

    def setInfo( self, data ):
        self.info = json.loads( data )


class pushover:
    """Class that handles Pushover actions"""

    session    = None
    userAgent  = 'curl/7.54'

    db         = None
    colNames   = None
    dbTable    = 'po_messages'

    apiVersion = 1
    baseUrl    = 'https://api.pushover.net/{version}/'.format( version = str( apiVersion ) )
    baseUrl   += '{location}'

    app        = None
    users      = []
    receipts   = []

    def __init__( self, app_tkn=None, user_tkn=None ):
        self.session = requests.session()
        self.session.headers = { 'User-Agent': self.userAgent }
        if app_tkn != None:
            self.app = app( app_tkn )
        else:
            app_tkn = os.getenv( 'PUSHOVER_APP' )
            if app_tkn == None:
                app_tkn = input( '{d}: '.format( d='Input your API token: ' ) )
            self.app = app( app_tkn )
        if user_tkn != None:
            self.users.append( user_tkn )
        else:
            user_tkn = os.getenv( 'PUSHOVER_USERS' )
            if user_tkn == None:
                user_tkn = input( '{d}: '.format( d='Input your User token: ' ) )
                self.users.append( user( user_tkn ) )
            else:
                user_tkn = json.loads( user_tkn )
                for u in user_tkn:
                    self.users.append( user( u ) )

    def setDB( self, db ):
        self.db = db
        db.startAction()
        sql = 'SELECT name FROM pragma_table_info( \'{dbTable}\' ) ORDER BY cid;'.format( dbTable=self.dbTable )
        db.execute( sql )
        self.colNames = [ n[0] for n in db.fetchall() ]
        db.close()

    def getApiInfo( self, obj ):
        rsp = self.session.get( obj.apiUrl )
        if rsp.status_code == 200:
            obj.setInfo( rsp.text )

    def addUser( self, user_tkn, device=None ):
        self.user.append( user( user( user_tkn, device ) ) )

    def sendMessage( self, message, title=None, expire=None, retry=None, device=None, sound=None, url=None, url_title=None, attachment=None, timestamp=None ):
        self.messageAll( message=message, title=title, expire=expire, retry=retry, device=device, sound=sound, url=url, url_title=url_title, attachment=attachment, timestamp=timestamp )

    def sendPrioMessage( self, message, title=None, expire=None, retry=None, device=None, sound=None, url=None, url_title=None, attachment=None, timestamp=None ):
        self.messageAll( message=message, title=title, priority=1, expire=expire, retry=retry, device=device, sound=sound, url=url, url_title=url_title, attachment=attachment, timestamp=timestamp )

    def sendConfirmPrioMessage( self, message, title=None, expire=None, retry=None, device=None, sound=None, url=None, url_title=None, attachment=None, timestamp=None ):
        self.messageAll( message=message, title=title, priority=2, expire=expire, retry=retry, device=device, sound=sound, url=url, url_title=url_title, attachment=attachment, timestamp=timestamp )

    def messageAll( self, message, title=None, priority=0, expire=None, retry=None, device=None, sound=None, url=None, url_title=None, attachment=None, timestamp=None ):
        for user in self.users:
            self.message( message=message, user=user, title=title, priority=2, expire=expire, retry=retry, device=device, sound=sound, url=url, url_title=url_title, attachment=attachment, timestamp=timestamp )

    def message( self, message, user, title=None, priority=0, expire=None, retry=None, device=None, sound=None, url=None, url_title=None, attachment=None, timestamp=None ):

        apiUrl = self.baseUrl.format( location="messages.json" )

        data   = {
            'token'   : self.app.token,
            'user'    : user.token,
            'message' : message
        }

        if title != None:
            data[ 'title' ] = title
        if priority != 0:
            data[ 'priority' ] = priority
            if expire == None:
                expire =  10800 # maximum value: 10800
            if retry == None:
                retry =  60 # minimum value: 30
        if expire != None:
            data[ 'expire' ] = expire
        if retry != None:
            data[ 'retry' ] = retry
        if device != None:
            data[ 'device' ] = device
        if sound != None:
            data[ 'sound' ] = sound
        if url != None:
            data[ 'url' ] = url
        if url_title != None:
            data[ 'url_title' ] = url_title
        if attachment != None:
            data[ 'attachment' ] = attachment
        if timestamp != None:
            data[ 'timestamp' ] = timestamp

        if self.db != None:
            db_data = {}
            for key in data:
                if key in self.colNames:
                    db_data[ key ] = data[ key ]
            sql = 'INSERT INTO {dbTable} ({colNames}) VALUES ({valPh});'.format( dbTable=self.dbTable, colNames=', '.join( db_data.keys() ), valPh=', '.join( [ '?' ] * len( db_data ) ) )
            self.db.fullExecute( sql, list(db_data.values()) )
            db_id = self.db.lastrowid()

        rsp = self.session.post(
            apiUrl,
            data = json.dumps( data ),
            headers={'content-type':'application/json'}
        )

        sql = 'UPDATE {dbTable} SET api_rc = ? WHERE id = ?;'.format( dbTable=self.dbTable )
        self.db.fullExecute( sql, [ rsp.status_code, db_id ] )

        if rsp.status_code == 200:
            data = json.loads( rsp.text )
            if 'receipt' in data:
                self.receipts.append( receipt( data[ 'receipt' ], self.app.token ) )
                sql = 'UPDATE {dbTable} SET receipt = ? WHERE id = ?;'.format( dbTable=self.dbTable )
                self.db.fullExecute( sql, [ data[ 'receipt' ], db_id ] )

    def checkUnconfirmedPrio( self ):
        sql = "SELECT * FROM {dbTable} WHERE priority = 2 AND receipt IS NOT NULL AND confirmation IS NULL;".format( dbTable=self.dbTable )
        self.db.startAction()
        self.db.execute( sql )
        allUnconfirmed = self.db.fetchallNamed()
        self.db.close()
        for uc in allUnconfirmed:
            apiUrl = self.baseUrl.format( location="receipts/{receipt}.json?token={token}".format( receipt=uc[ 'receipt' ], token=self.app.token ) )
            rsp = self.session.get( apiUrl )
            if rsp.status_code == 200:
                data = json.loads( rsp.text )
                if data['acknowledged'] == True:
                    confirmationDate = datetime.datetime.fromtimestamp( data[ 'acknowledged_at' ] )
                    sql = 'UPDATE {dbTable} SET receipt_info = ?, confirmation = ? WHERE id = ?'.format( dbTable=self.dbTable )
                    self.db.fullExecute( sql, [ json.dumps( data, indent=4 ), confirmationDate.strftime('%Y-%m-%d %H:%M:%S'), uc[ 'id' ] ] )
                else:
                    sql = 'UPDATE {dbTable} SET receipt_info = ? WHERE id = ?'.format( dbTable=self.dbTable )
                    self.db.fullExecute( sql, [ json.dumps( data, indent=4 ), uc[ 'id' ] ] )

