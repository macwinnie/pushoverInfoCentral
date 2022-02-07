#!/usr/bin/env python3

###
## ensure that all requirements are installed and all directories exist
###
from helper import *
init()

###
## initiate Database
###
import database
db = database.db()

###
## initiate Pushover
###
import pushover
po = pushover.pushover()
po.setDB( db )

###
## import system libraries
###
import os, datetime, json, time, psutil

###
## get variables from env
###
lensleep  = int( os.getenv( 'SLEEP', 60 ) )
date_f    = "%d.%m.%Y %H:%M.%S"

###
## set timezone
###
os.environ['TZ'] = os.getenv( 'TIMEZONE', 'Europe/Berlin' )
try:
    time.tzset()
except:
    po.sendConfirmPrioMessage( 'ERROR on setting timezone {}'.format( os.getenv( 'TZ' ) ) )

###
## main function
###

import watcher
watcher = watcher.__all__

watchers = []
for w in watcher:
    watchers.append( __import__( "watcher.{module}".format( module=w ), locals(), globals(), [ "watch" ] ) )

while True:
    for module in watchers:
        module.watch( db, po )
    time.sleep( lensleep )
    # end this script if RAM is used more than 75 percent
    if psutil.virtual_memory().percent > 75:
        break
