#!/usr/bin/env python3

import os, sys, subprocess, atexit

###
## Helper function while development: python CLI history
###
def history ( lineNumbers=False ):
    import readline
    if lineNumbers:
        formatstring = '{0:4d}  {1!s}'
    else:
        formatstring = '{1!s}'
    for i in range( 1, readline.get_current_history_length() + 1 ):
        print( formatstring.format( i, readline.get_history_item( i ) ) )

###
## function to init the system
###
def init ():
    hello_script()

    print( 'Starting with installation of requirements ...' )
    subprocess.check_call( [ sys.executable, '-m', 'pip' ] + 'install -r requirements.txt'.split(), stdout=open( os.devnull, 'wb' ), stderr=open(os.devnull, 'wb') )
    print( '... installation of requirements finished.' )
    print()

    # fetch variables from ENV
    from dotenv import load_dotenv
    load_dotenv()

###
## start script if lockfile not existent
###
lockfile = '.watch.lock'
def hello_script():
    if os.path.isfile( lockfile ):
        os._exit( 1 )
    open( lockfile, 'a' ).close()
    atexit.register( goodbye_script )

###
## end script and remove lockfile
###
def goodbye_script():
    if os.path.exists( lockfile ):
        os.remove( lockfile )
