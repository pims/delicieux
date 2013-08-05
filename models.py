# -*- coding: utf-8 -*-
'''
    delicious.models
    -----------
'''

from google.appengine.ext import ndb
from collections import Counter
from utils import to_delicious_date_format
import hashlib

class Post(ndb.Model):
    '''Post represents a Bookmark'''

    href = ndb.StringProperty(required=True)
    description = ndb.StringProperty(indexed=False, required=True)
    tags = ndb.StringProperty(repeated=True)

    time = ndb.DateTimeProperty(auto_now_add=True)
    meta = ndb.StringProperty(default='')
    extended = ndb.TextProperty()
    private = ndb.BooleanProperty(indexed=False, default=False)

    def to_dict(self):
        '''Serializes to a dict with names matching delicious API'''
        return {
            'href' : self.href,
            'dt' : to_delicious_date_format(self.time),
            'description' : self.description,
            'extended' : self.extended,
            'hash' : hashlib.md5(self.href).hexdigest(),
            'meta' : self.meta,
            'tags' : ' '.join(self.tags)
        }

    @classmethod
    def get_by_ids(cls, list_of_ids):
        '''Multi get posts by id (md5 hash)

        :param list_of_ids: list of md5 hashes to retrieve
        :type list_of_ids: list
        :rtype: list 
        '''
        keys = [ndb.Key(cls, idx) for idx in list_of_ids]
        posts = ndb.get_multi(keys)
        return [post.to_dict() for post in posts]

    @classmethod
    def get_by_tags(cls, list_of_tags, limit=100):
        '''Multi get posts by tags

        :param list_of_tags: list of tags to filter posts by
        :type list_of_tags: list
        :param limit : maximum number of posts to retrieve
        :type limit: int
        :rtype: list
        '''
        limit = min(100, limit)
        qry = cls.query(cls.tags.IN(list_of_tags))
        return [post.to_dict() for post in qry.fetch(limit)]

    @classmethod
    def get_recent(cls, tag = None, limit = 100):
        '''Multi get posts by tags

        :param tag: tag to filter posts by
        :type tag: str
        :param limit : maximum number of posts to retrieve
        :type limit: int
        :rtype: list
        '''
        limit = min(100, limit)
        qry = cls.query()
        if tag is not None:
            qry = qry.filter(cls.tags == tag)

        return [post.to_dict() for post in qry.fetch(limit)]

    @classmethod
    def counts_by_date(cls, tag=None):
        '''Get counts by date

        :param tag: tag to filter posts by
        :type tag: str
        :rtype: list
        '''
        qry = cls.query()
        if tag is not None:
            qry = qry.filter(cls.tags == tag)

        # TODO : Persist results to datastore
        counter = Counter()
        
        for post in qry.fetch(1000):
            key = post.time.strftime('%Y-%m-%d')
            counter[key] += 1

        dates = [dict(count=str(v), date=k) for k, v in counter.iteritems()]
        
        dates.sort(key = lambda x: x['date'], reverse=True)
        return dates

    @classmethod
    def counts_by_tag(cls):
        '''Get counts by tag

        :rtype: list
        '''
        qry = cls.query()
        counter = Counter()
        for post in qry.fetch(1000):
            for tag in post.tags:
                counter[tag] += 1

        dates = [dict(count=str(v), tag=k) for k,v in counter.iteritems()]
        dates.sort(key = lambda x: x['tag'],reverse=True)
        return dates

    @classmethod
    def get_all(cls, tag=None, limit=1000):
        '''Multi get all posts

        :param tag: tag to filter posts by
        :type tag: str
        :param limit : maximum number of posts to retrieve
        :type limit: int
        :rtype: list
        '''
        limit = min(1000, limit)
        qry = cls.query()
        if tag is not None:
            qry = qry.filter(cls.tags == tag)

        return [post.to_dict() for post in qry.fetch(limit)]

    @classmethod
    def get_all_hashes(cls, tag=None, limit=1000):
        '''Multi get all posts hashes

        :param tag: tag to filter posts by
        :type tag: str
        :param limit : maximum number of posts to retrieve
        :type limit: int
        :rtype: list
        '''
        qry = cls.query()
        posts = qry.fetch(limit, projection=[cls.href, cls.meta])
        return [dict(meta=post.meta, url=post.href) for post in posts]