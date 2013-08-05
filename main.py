# -*- coding: utf-8 -*-
'''
    delicieux.main
    -----------

    Delicieux aims to provide a self hosted bookmarking API
    100% compatible with the Delicious.com and Pinboard.in APIs

'''

import webapp2
import hashlib
from datetime import datetime

import settings
from utils import results
from utils import auth_required
from utils import to_delicious_date_format

from google.appengine.ext import ndb
from models import Post



class BaseRequestHandler(webapp2.RequestHandler):
    '''BaseRequestHandler'''

    @property
    def context(self):

        return {
            'user' : self.app.config['auth'][0],
            'dt' : datetime.now().strftime('%Y-%m-%d')
        }

    def write_xml(self, xml_string):
        '''prepends the xml doctype to the xml_string

        :param xml_string: string representing the xml response
        :type xml_string: str
        '''
        self.response.out.write('''<?xml version="1.0" encoding="UTF-8"?>''')
        self.response.out.write(xml_string)
        return

class PostsUpdateHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns the last update time for the user, as well as the number of new items
        in the user’s inbox since it was last visited.
        
        Use this before calling posts/all to see if the data has changed since the last fetch.
        '''

        update = {
            'code' : '200',
            'inboxnew' : '0', # not implemented
            'message' : 'success',
            'time' : to_delicious_date_format(datetime.now())
            }

        self.write_xml(results('update', [], update))

class PostsAddHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Add a post to Delicious.

        Arguments:

        &url={URL}
        (required) the url of the item.

        &description={...}
        (required) the description of the item.

        &extended={...}
        (optional) notes for the item.

        &tags={...}
        (optional) tags for the item (comma delimited).

        &dt={CCYY—MM—DDThh:mm:ssZ}
        (optional) datestamp of the item (format “CCYY—MM—DDThh:mm:ssZ”).
        Requires a LITERAL “T” and “Z” like in ISO8601 at 
        http://www.cl.cam.ac.uk/~mgk25/iso—time.html for Example: "1984—09—01T14:21:31Z"

        &replace=no
        (optional) don’t replace post if given url has already been posted.

        &shared=no
        (optional) make the item private
        '''

        url = self.request.get('url', default_value=None)
        description = self.request.get('description', default_value=None)

        if url is None or description is None:
            # Not returning an error code for compatibility with delicious API
            # self.error(500)
            self.write_xml(results('result', [], {'code' : 'something went wrong'}))
            return

        extended = self.request.get('extended')
        tags = self.request.get('tags')
        
        dt = self.request.get('dt')
        replace = self.request.get('replace')
        shared = self.request.get('shared')

        # cleaning
        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%SZ') if dt else datetime.now()
        tags = tags.split() if tags else []
        replace = replace == 'yes' # replace is true iff replace == 'yes'
        shared = shared == 'yes'

        
        post = Post(
                id=hashlib.md5(url).hexdigest(),
                href=url,
                description=description,
                extended=extended,
                tags=tags,
                time=dt,
                private=shared)

        post.put()
        self.write_xml(results('result', [], {'code' : 'done'}))


class PostsDeleteHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Delete a post from Delicious.
        
        Arguments:

        &url={URL}
        (required) the url of the item.
        '''

        url = self.request.get('url', default_value=None)
        if url is None:
            self.write_xml(results('result', [], {'code' : 'url or md5 required'}))
        
        # encode to md5 only if not already a md5 hash
        key = hashlib.md5(url).hexdigest() if url.startswith('http') else url
        post_key = ndb.Key('Post', key)
        post_key.delete()

        self.write_xml(results('result', [], {'code' : 'done'}))

class PostsGetHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns one or more posts on a single day matching the Arguments.
        If no date or url is given, most recent date will be used.

        Arguments:

        &tag={TAG}+{TAG}+...+{TAG}
        (optional) Filter by this tag.

        &dt={CCYY—MM—DDThh:mm:ssZ}
        (optional) Filter by this date, defaults to the most recent date on which bookmarks were saved.

        &url={URL}
        (optional) Fetch a bookmark for this URL, regardless of date.  Note: Be sure to URL—encode 
        the argument value.

        &hashes={MD5}+{MD5}+...+{MD5}
        (optional) Fetch multiple bookmarks by one or more URL MD5s regardless of date, separated by 
        URL—encoded spaces (ie. ‘+’).

        &meta=yes
        (optional) Include change detection signatures on each item in a ‘meta’ attribute.  Clients 
        wishing to maintain a synchronized local store of bookmarks should retain the value of this 
        attribute — its value will change when any significant field of the bookmark changes.
        '''

        tags = self.request.get('tag')
        url = self.request.get('url')
        hashes = self.request.get('hashes')
        meta = self.request.get('meta')

        # TODO: implement filtering by date: self.request.get('dt')

        #normalize
        hashes = set(hashes.split()) if hashes else []
        tags = tags.split() if tags else []
        meta = meta == 'yes'

        if url:
            url = hashlib.md5(url).hexdigest()
            hashes.add(url)
                
        res = Post.get_by_ids(hashes)
        if tags:
            res.extend(Post.get_by_tags(tags))
        
        context = {
            'tag' : ' '.join(tags),
        }
        context.update(self.context)

        xml_response = results('posts', res, context)
        # TODO: cache for N minutes
        self.write_xml(xml_response)

class PostsRecentHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns a list of the most recent posts, filtered by argument. Maximum 100.

        Arguments:

        &tag={TAG}
        (optional) Filter by this tag.
        &count={1..100}
        (optional) Number of items to retrieve (Default:15, Maximum:100).
        '''

        tag = self.request.get('tag', default_value=None)
        count = self.request.get('count')

        count = min(int(count), 100) if count else 15


        res = Post.get_recent(tag, count)
        
        context = {
            'tag' : tag,
        }
        context.update(self.context)

        xml_response = results('posts', res, context)
        # TODO: cache for N minutes
        self.write_xml(xml_response)


class PostsDatesHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns a list of dates with the number of posts at each date.

        Arguments:

        &tag={TAG}
        (optional) Filter by this tag
        '''
        tag = self.request.get('tag', default_value=None)

        dates = Post.counts_by_date(tag)
        context = {
            'tag' : tag if tag is not None else ''
        }
        context.update(self.context)
        xml_response = results('dates', dates, context)
        # TODO : cache for N minutes
        self.write_xml(xml_response)

class PostsAllHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns all posts. Please use sparingly. Call the update function to see if you need
        to fetch this at all.

        Arguments:

        &tag={TAG}
        (optional) Filter by this tag.

        &start={xx}
        (optional) Start returning posts this many results into the set.

         &results={xx}
        (optional) Return this many results.

        &fromdt={CCYY-MM-DDThh:mm:ssZ}
        (optional) Filter for posts on this date or later

        &todt={CCYY-MM-DDThh:mm:ssZ}
        (optional) Filter for posts on this date or earlier

        &meta=yes
        (optional) Include change detection signatures on each item in a 
        'meta' attribute. Clients wishing to maintain a synchronized local 
        store of bookmarks should retain the value of this attribute - its 
        value will change when any significant field of the bookmark changes.
        

        Returns a change manifest of all posts. Call the update function to see if you need
        to fetch this at all.
        This method is intended to provide information on changed bookmarks without
        the necessity of a complete download of all post data.
        Each post element returned offers a url attribute containing an URL MD5,
        with an associated meta attribute containing the current change detection
        signature for that bookmark.
        '''

        tag = self.request.get('tag', default_value=None)
        count = self.request.get('results')

        count = int(count) if count else 1000
        
        if 'hashes' in self.request.params:
            res = Post.get_all_hashes(tag, count)
        else:
            res = Post.get_all(tag, count)


        context = {
            'tag' : tag if tag is not None else ''
        }
        context.update(self.context)

        xml_response = results('posts', res, context)
        self.write_xml(xml_response)


class PostsSuggestHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns a list of popular tags, recommended tags and network tags for a user.
            This method is intended to provide suggestions for tagging a particular url.

        Arguments:

        &url={URL}
        (required) URL for which you'd like suggestions

        Ex:
        <suggest>
            <popular>yahoo!</popular>
            <popular>yahoo</popular>
            <popular>web</popular>
            <popular>tools</popular>
            <popular>searchengines</popular>
            <recommended>yahoo!</recommended>
            <recommended>yahoo</recommended>
            <recommended>web</recommended>
            <recommended>tools</recommended>
            <recommended>search</recommended>
            <recommended>reference</recommended>
            <recommended>portal</recommended>
            <recommended>news</recommended>
            <recommended>music</recommended>
            <recommended>internet</recommended>
            <recommended>home</recommended>
            <recommended>games</recommended>
            <recommended>entertainment</recommended>
            <recommended>email</recommended>
            <network>for:Bernard</network>
            <network>for:britta</network>
            <network>for:deusx</network>
            <network>for:joshua</network>
            <network>for:stlhood</network>
            <network>for:theteam</network>
        </suggest>
        '''

        self.write_xml(results('suggest', [], {}))


class TagsGetHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Returns a list of tags and number of times used by a user.

        <tags>
            <tag count="1" tag="activedesktop" />
            <tag count="1" tag="business" />
            <tag count="3" tag="radio" />
            <tag count="5" tag="xml" />
            <tag count="1" tag="xp" />
            <tag count="1" tag="xpi" />
        </tags>
        '''

        res = Post.counts_by_tag()
        xml_response = results('tags', res, {})
        self.write_xml(xml_response)


class TagsDeleteHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Delete an existing tag.

        Arguments:

        &tag={TAG}
        (required) Tag to delete
        '''
        tag = self.request.get('tag', None)

        # TODO : DELETE FROM DB
        xml_response = '''<result>done</result>'''
        self.write_xml(xml_response)

class TagsRenameHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        '''Rename an existing tag with a new tag name.

        Arguments:

        &old={TAG}
        (required) Tag to rename.
  
        &new={TAG}
        (required) New tag name.
        '''

        old_tag = self.request.get('old', None)
        new_tag = self.request.get('new', None)

        xml_response = '''<result>done</result>'''
        self.write_xml(xml_response)


class TagsBundleAllRenameHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        self.abort(501)

class TagsBundleAllHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        self.abort(501)

class TagsBundleSetHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        self.abort(501)

class TagsBundleDeleteHandler(BaseRequestHandler):
    @auth_required
    def get(self):
        self.abort(501)

urls = [
    ('/v1/posts/update', PostsUpdateHandler),
    ('/v1/posts/add', PostsAddHandler),
    ('/v1/posts/delete', PostsDeleteHandler),
    ('/v1/posts/get', PostsGetHandler),
    ('/v1/posts/recent', PostsRecentHandler),
    ('/v1/posts/dates', PostsDatesHandler),
    ('/v1/posts/all', PostsAllHandler),
    ('/v1/posts/suggest', PostsSuggestHandler),
    ('/v1/tags/get', TagsGetHandler),
    ('/v1/tags/delete', TagsDeleteHandler),
    ('/v1/tags/rename', TagsRenameHandler),
    ('/v1/tags/bundles/all', TagsBundleAllHandler),
    ('/v1/tags/bundles/set', TagsBundleSetHandler),
    ('/v1/tags/bundles/delete', TagsBundleDeleteHandler)]



app = webapp2.WSGIApplication(urls, debug=settings.debug, config=settings.config)