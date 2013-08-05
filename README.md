DELICIEUX
=========

Delicieux provides a self hosted bookmarking API compatible with Delicious - and probably Pinboard – clients.

At the moment Delicieux is tightly coupled to the Google App Engine platform. This should change in the future.

GETTING STARTED
===============

1. Register an application on Google App Engine [https://appengine.google.com/](https://appengine.google.com/)
2. Clone this repo
3. Replace the `application` name in `app.yaml`
4. Change the user/password in settings.py
5. Deploy to Google App Engine


UPDATE
======

	https://api.delicious.com/v1/posts/update - Check to see when a user last posted an item

POSTS
=====

	https://api.delicious.com/v1/posts/add? - add a new bookmark
	https://api.delicious.com/v1/posts/delete? - delete an existing bookmark
	https://api.delicious.com/v1/posts/get? - get bookmark for a single date, or fetch specific items
	https://api.delicious.com/v1/posts/recent? - fetch recent bookmarks
	https://api.delicious.com/v1/posts/dates? - list dates on which bookmarks were posted
	https://api.delicious.com/v1/posts/all? - fetch all bookmarks by date or index range
	https://api.delicious.com/v1/posts/all?hashes - fetch a change detection manifest of all items
	https://api.delicious.com/v1/posts/suggest - fetch popular, recommended and network tags for a specific url


TAGS
====

	https://api.delicious.com/v1/tags/get - fetch all tags
	https://api.delicious.com/v1/tags/delete? - delete a tag from all posts
	https://api.delicious.com/v1/tags/rename? - rename a tag on all posts


TAG BUNDLES (NOT IMPLEMENTED)
===========

	https://api.delicious.com/v1/tags/bundles/all? - fetch tag bundles
	https://api.delicious.com/v1/tags/bundles/set? - assign a set of tags to a bundle
	https://api.delicious.com/v1/tags/bundles/delete? - delete a tag bundle
