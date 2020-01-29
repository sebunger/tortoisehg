import os, sys

bin_path = os.path.dirname(sys.executable)

nofork = True
if 'THG_OSX_APP' in os.environ:
    license_path = os.path.join(os.environ['RESOURCEPATH'], 'COPYING.txt')
    locale_path = os.path.join(os.environ['RESOURCEPATH'], 'locale')
    icon_path = os.path.join(os.environ['RESOURCEPATH'], 'icons')


