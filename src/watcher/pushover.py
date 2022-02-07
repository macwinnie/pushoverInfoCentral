#!/usr/bin/env python3

"""Watcher that fetches confirmation dates for prio 2 messages"""

def watch( database, pushover ):
    pushover.checkUnconfirmedPrio()
