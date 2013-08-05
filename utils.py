# -*- coding: utf-8 -*-
'''
    delicieux.utils
    -----------
'''

from lxml import etree
import base64

def to_delicious_date_format(dt_obj):
    '''Formats a date according to the delicious API format

    :param dt : datetime object
    :type dt : datetime
    :rtype: str
    '''
    return dt_obj.strftime('%Y-%m-%dT%H:%M:%SZ')


def results(root_node, children, root_node_attributes):
    '''Construct an XML document and serializes it

    Only supports one level of nesting

    :param root_node: name of the root_node
    :type root_node: str
    :param children: list of children of the root node
    :type children: list
    :param root_node_attributes: list of attributes for the root node
    :type root_node_attributes: dict
	:rtype: str
	'''
    root = etree.Element(root_node, **root_node_attributes)
    for child in children:
        child_node = etree.SubElement(root, root_node[:-1], **child)
    return etree.tostring(root)

def auth_required(handler):
    '''Decorator to require authentication for certain urls'''

    def check_login(self, *args, **kwargs):
        '''Validates Basic Authentication credentials'''
        if 'Authorization' in self.request.headers:
            _, encoded_value = self.request.headers['Authorization'].split()
            username, password = base64.decodestring(encoded_value).split(':')
            if (username, password) == self.app.config['auth']:
                return handler(self, *args, **kwargs)
            
        return self.write_xml(results('result', [], {'code' : 'access denied'}))
    return check_login