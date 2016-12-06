#!/var/pythonapps/py3/bin/python3
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/pythonapps/CS/")
def execfile(filename):
    globals = dict( __file__ = filename )
    exec( open(filename).read(), globals )

activate_this = '/var/pythonapps/py3/bin/activate_this.py'
execfile( activate_this )

from display import app as application
