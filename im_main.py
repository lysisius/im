import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

import pymongo
import im_userDAO
import im_sessionDAO
import im_inboxDAO
import re
import urllib

define("port", default=8887, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        # get cookie
        cookie = self.get_cookie('session')
        # get username
        username = sessions.get_username(cookie)
        # get online usernames
        all_users = sessions.get_sessions()
        # get inbox, contacts, groups

        user = users.get_user(username)
        if not user:
            self.redirect('/signup')
        else:
            groups = user['groups']
            messages = inbox.get_msg(username, groups)
            self.render('im_main.html', 
                        username=username, 
                        messages=messages,
                        all_users = all_users,
                        groups=groups)

class MsgHandler(tornado.web.RequestHandler):
    def post(self):
        # get cookie
        cookie = self.get_cookie('session')
        # get username
        username = sessions.get_username(cookie)
        # get user
        # user = users.
        dst = self.get_argument('dst', '') 
        body = self.get_argument('body', '')
        # users.send_msg(username, dst, body)
        inbox.send(dst, username, body)
        self.redirect('/')

    def get(self, action, msgid):
        action = urllib.unquote(action)
        msgid = urllib.unquote(msgid)
        print action, msgid
        # get cookie
        cookie = self.get_cookie('session')
        # get username
        username = sessions.get_username(cookie)
        
        if action == 'del':
            print 'hello'
            inbox.del_msg(msgid)
        elif action == 'read':
            pass
        self.redirect('/')

class GrpMsgHandler(tornado.web.RequestHandler):
    def post(self):
        # get cookie
        cookie = self.get_cookie('session')
        # get username
        username = sessions.get_username(cookie)
        # get user
        dst = self.get_argument('grpdst', '') 
        body = self.get_argument('grpbody', '')

        inbox.send(dst, username, body, grp=True)
        self.redirect('/')

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('im_login.html', username='', login_error='')
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        print "user submitted ", username, "pass ", password

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

class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        cookie = self.get_cookie('session')
        sessions.end_session(cookie)
        self.set_cookie('session', '')
        self.redirect('/signup')

class SignupHandler(tornado.web.RequestHandler):
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
            # self.render('im_main.html', username=username, messages=test_msgs)
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
    users = im_userDAO.UserDAO(database)
    sessions = im_sessionDAO.SessionDAO(database)
    inbox = im_inboxDAO.InboxDAO(database)

    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[
            (r"[/ ]", IndexHandler), 
            (r"/login", LoginHandler), 
            (r"/logout", LogoutHandler), 
            (r"/msg/new", MsgHandler), 
            (r"/msg/(del)/([^/]+)", MsgHandler), 
            # (r"/msg/del/([^/]+)", MsgHandler), 
            (r"/grpmsg/new", GrpMsgHandler), 
            (r'/signup', SignupHandler)], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret="bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
        debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

