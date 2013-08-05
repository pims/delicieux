# -*- coding: utf-8 -*-
'''
    delicieux.settings
    -----------
'''

import os

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
config = {'auth' : ('user', 'password')}