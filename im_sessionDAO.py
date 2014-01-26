import sys
import random
import string

# The session Data Access Object handles interactions with the sessions collection
class SessionDAO:
    def __init__(self, database):
        self.db = database
        self.sessions = database.sessions
        self.sessions_cache = {}
        cursor = self.sessions.find()
        print 'DB read: sessions'
        for session in cursor:
            session_id = session.get('_id')
            self.sessions_cache[session_id] = session

    # will start a new session id by adding a new document to the sessions collection
    # returns the sessionID or None
    def start_session(self, username):
        # clear the existing session for the same user
        session = self.get_session_by_username(username)
        if session:
            self.end_session(session['_id'])
        session_id = self.get_random_str(32)
        session = {'username': username, '_id': session_id}
        try:
            self.sessions.insert(session, safe=True)
            print 'DB write: add session'
        except:
            print "Unexpected error on start_session:", sys.exc_info()[0]
            return None

        self.sessions_cache[session_id] = session 
        return str(session['_id'])

    # will send a new user session by deleting from sessions table
    def end_session(self, session_id):
        if session_id is None:
            return
        self.sessions.remove({'_id': session_id})
        print 'DB write: del session'
        del self.sessions_cache[session_id]
        return

    def get_session_by_username(self, username):
        """
        it's a bit more tedious to use cache for this one
        """
        for session_id in self.sessions_cache:
            session = self.sessions_cache[session_id]
            if session['username'] == username:
                return session
        return None

    # if there is a valid session, it is returned
    def get_session(self, session_id):
        if session_id is None:
            return None
        return self.sessions_cache.get(session_id)

    def get_sessions(self):
        return self.sessions_cache.values()

    # get the username of the current session, or None if the session is not valid
    def get_username(self, session_id):
        session = self.sessions_cache.get(session_id)
        if session is None:
            return None
        else:
            return session['username']

    def get_random_str(self, num_chars):
        random_string = ""
        for i in range(num_chars):
            random_string = random_string + random.choice(string.ascii_letters)
        return random_string
