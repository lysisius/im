import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

import pymongo
import asyncmongo
import im_userDAO
import im_sessionDAO
import im_inboxDAO
import re
import urllib

define("port", default=8887, help="run on the given port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        # get cookie
        cookie = self.get_cookie('session')
        # get username
        username = sessions.get_username(cookie)
        return username
    # def _handle_request_exception(self, e):
    #     logging.error('error')

class IndexHandler(BaseHandler):
    # @tornado.web.asynchronous
    def get(self):
        username = self.get_current_user()
        # get online usernames
        all_users = sessions.get_sessions()
        # get inbox, contacts, groups
        user = users.get_user(username)
        if not user:
            self.redirect('/signup')
            return
        groups = users.get_groups_membership(username)

        """
        TODO: the problem here is that index page gets requested
        all the time. the next step is to take the inbox
        page out
        """
        messages = inbox.get_msg(username, groups)
        msg_new, msg_read = [], []
        # messages is not a list but a pymongo cursor, have to loop through
        # manually. list comprehension doesn't work
        for m in messages:
            if not m['read']:
                msg_new.append(m)
            else:
                msg_read.append(m)
                
        self.render('im_main.html', 
                    username=username, 
                    msg_new=msg_new,
                    msg_read=msg_read,
                    all_users=all_users,
                    groups=groups)

class MsgHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        username = self.get_current_user()
        # get user
        # user = users.
        dst = self.get_argument('dst', '') 
        body = self.get_argument('body', '')
        # users.send_msg(username, dst, body)
        def _cb(r, error):
            print 'err: ', error
            assert not error
            # self.redirect('/')
        inbox.send(dst, username, body, send_cb=_cb)
        self.redirect('/')

    def get(self, action, msgid):
        action = urllib.unquote(action)
        msgid = urllib.unquote(msgid)
        print action, msgid
        username = self.get_current_user()
        
        if action == 'del':
            inbox.del_msg(msgid)
        elif action == 'read':
            inbox.read_msg(msgid)
        self.redirect('/')

class GrpMemberHandler(BaseHandler):
    def get(self, action, grpname):
        action = urllib.unquote(action)
        grpname = urllib.unquote(grpname)

        username = self.get_current_user()

        if action == 'join':
            users.join_group(username, grpname)
        elif action == 'leave':
            users.leave_group(username, grpname)
        self.redirect('/')

class GrpMsgHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        username = self.get_current_user()
        # get user
        dst = self.get_argument('grpdst', '') 
        body = self.get_argument('grpbody', '')

        def _cb(r, error):
            print 'err: ', error
            assert not error
            # self.redirect('/')
        inbox.send(dst, username, body, grp=True, send_cb=_cb)
        self.redirect('/')

class LoginHandler(BaseHandler):
    def get(self):
        self.render('im_login.html', username='', login_error='')
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        user_record = users.validate_login(username, password)
        if user_record:
            session_id = sessions.start_session(user_record['_id'])
            if not session_id:
                self.redirect('/internal_error')
            cookie = session_id
            self.set_cookie('session', cookie)
            self.redirect('/')
        else:
            # potential escape needed
            self.render('im_login.html', username=username, login_error='Invalid Login')

class LogoutHandler(BaseHandler):
    def get(self):
        cookie = self.get_cookie('session')
        sessions.end_session(cookie)
        self.set_cookie('session', '')
        self.redirect('/signup')

class ErrorHandler(BaseHandler):
    def get(self):
        self.write('error')
    def post(self):
        self.write('error')

class SignupHandler(BaseHandler):
    def get(self):
        self.render('im_signup.html', username='', username_error='',
            password_error='', verify_error='', email_error='', email='')
    def post(self):
        email = self.get_argument('email', '')
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        verify = self.get_argument('verify')

        # need to escape these
        errors = {'username': username, 'email': email}
        if validate_signup(username, password, verify, email, errors):

            if not users.add_user(username, password, email):
                # this was a duplicate
                errors['username_error'] = "Username already in use. Please choose another"
                self.render('im_signup.html', 
                            username=username, 
                            username_error=errors['username_error'],
                            password_error='', 
                            verify_error='', 
                            email_error='', email=email)

            session_id = sessions.start_session(username)
            print session_id
            self.set_cookie("session", session_id)
            self.redirect("/")
        else:
            print "user did not validate"
            self.render('im_signup.html', username=username,
                        username_error=errors['username_error'],
                        verify_error=errors['verify_error'],
                        password_error=errors['password_error'],
                        email_error=errors['email_error'],
                        password='', email=email)

def validate_signup(username, password, verify, email, errors):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASS_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

    errors['username_error'] = ""
    errors['password_error'] = ""
    errors['verify_error'] = ""
    errors['email_error'] = ""

    if not USER_RE.match(username):
        errors['username_error'] = "invalid username. try just letters and numbers"
        return False

    if not PASS_RE.match(password):
        errors['password_error'] = "invalid password."
        return False
    if password != verify:
        errors['verify_error'] = "password must match"
        return False
    if email != "":
        if not EMAIL_RE.match(email):
            errors['email_error'] = "invalid email address"
            return False
    return True

if __name__ == "__main__":
    connection_string = "mongodb://localhost"
    connection = pymongo.MongoClient(connection_string)
    database = connection.chat

    asyncdb = asyncmongo.Client(
        pool_id='test', host='localhost', port=27017, dbname='chat')


    users = im_userDAO.UserDAO(database, asyncdb)
    sessions = im_sessionDAO.SessionDAO(database)
    inbox = im_inboxDAO.InboxDAO(database, asyncdb)

    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[
            (r"/", IndexHandler), 
            (r"/login", LoginHandler), 
            (r"/logout", LogoutHandler), 
            (r"/msg/new", MsgHandler), 
            (r"/msg/(del|read)/([^/]+)", MsgHandler), # use brackets!  
            (r"/grp/(join|leave)/([^/]+)", GrpMemberHandler), # use brackets!  
            (r"/grpmsg/new", GrpMsgHandler), 
            (r'/signup', SignupHandler), 
            (r'/.*', ErrorHandler)], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret="bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
        debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

