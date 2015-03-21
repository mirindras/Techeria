import cgi
import webapp2
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from webapp2_extras import sessions, auth
from models import User
from models import Comment
from models import Message
from models import ConnectionRequest
from models import ForumPost
from models import Skill
from models import Forum
import logging
import random
import string
import datetime
from BaseHandler import SessionHandler
from BaseHandler import login_required

class VoteHandler(SessionHandler):
  def post(self):
    post = cgi.escape(self.request.get('key'))
    change = int(cgi.escape(self.request.get('change')))
    voter = cgi.escape(self.request.get('voter'))
    post_key = ndb.Key(urlsafe=post)
    new_post = post_key.get()
    user_key = ndb.Key(urlsafe=voter)
    if change == 1:
      if user_key in new_post.down_voters:
        change+=1
        new_post.down_voters.remove(user_key);
      new_post.up_voters.append(user_key)
    else:
      if user_key in new_post.up_voters:
        change-=1
        new_post.up_voters.remove(user_key);
      new_post.down_voters.append(user_key)
    new_post.vote_count+=change
    new_post.put()

class ForumHandler(SessionHandler):
  """ Handles the forum """
  def get(self, forum_id):
    forum_id = forum_id.lower()
    user = self.user_model
    forum_posts = ForumPost.query(ForumPost.forum_name == forum_id)
    self.response.out.write(template.render('views/forum.html', {'viewer': user,
                                      'posts': forum_posts, 'forum_name': forum_id}))
  def post(self, forum_id):
    author = cgi.escape(self.request.get('author'))
    forum_name = cgi.escape(self.request.get('forum'))
    title = cgi.escape(self.request.get('title'))
    url = cgi.escape(self.request.get('url'))
    text = cgi.escape(self.request.get('text'))
    post = ForumPost()
    forum = Forum.query(Forum.name == forum_name).get()
    if forum != None:
      forum.posts += 1
    else:
      forum = Forum(name=forum_name, posts=1)
    forum.put()
    post.text = text
    post.author = author
    post.forum_name = forum_name
    post.title = title
    post.time = datetime.datetime.now() - datetime.timedelta(hours=8) #For PST
    post.url = url
    post.reference = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    post.put()
    self.redirect('/tech/{}'.format(forum_name))

class SubmissionHandler(SessionHandler):
  """Handles user submissions to forums"""
  @login_required
  def get(self):
    user = self.user_model
    forum_name = cgi.escape(self.request.get('forum_name'))
    self.response.out.write(template.render('views/submitPost.html', {'viewer': user, 'forum_name':forum_name}))

class ForumCommentHandler(SessionHandler):
  """retrieves the correct forum post"""
  def get(self, forum_id, post_reference):
    user = self.user_model
    post = ForumPost.query(ForumPost.forum_name == forum_id, ForumPost.reference == post_reference).get()
    comments = Comment.query(ancestor=post.key).fetch()
    self.response.out.write(template.render('views/forumComments.html', {'viewer': user, 'post':post, 'forum_name':forum_id, 'comments':comments}))
  def post(self, forum_id, post_reference):
    user = self.user_model
    post = ForumPost.query(ForumPost.forum_name == forum_id, ForumPost.reference == post_reference).get()
    text = cgi.escape(self.request.get('text'))
    sender = cgi.escape(self.request.get('sender'))
    recipient = cgi.escape(self.request.get('recipient'))
    comment = Comment(parent=post.key)
    comment.text = text
    comment.sender = sender
    comment.recipient = recipient
    comment.time = datetime.datetime.now() - datetime.timedelta(hours=8) #For PST
    comment.put()
    self.redirect('/tech/{}/{}'.format(forum_id, post_reference))

class ForumViewer(SessionHandler):
  def get(self):
    forums = Forum.query().order(-Forum.posts)
    self.response.out.write(template.render('views/forumViewer.html', {'viewer': self.user_model, 'forums':forums}))    

app = webapp2.WSGIApplication([
                               ('/tech/(\w+)', ForumHandler),
                               ('/submit', SubmissionHandler),
                               ('/tech/(\w+)/(\w+)', ForumCommentHandler),
                               ('/tech', ForumViewer),
                               ('/tech/', ForumViewer)
                               ], debug=True)
