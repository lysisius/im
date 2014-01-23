import hmac
import random
import string
import hashlib
import pymongo

class UserDAO:
    def __init__(self, db):
        self.db = db
        self.users = self.db.users
        self.SECRET = 'verysecret'

    def make_salt(self):
        salt = ""
        for i in range(5):
            salt = salt + random.choice(string.ascii_letters)
        return salt

    def make_pw_hash(self, pw,salt=None):
        if salt == None:
            salt = self.make_salt();
        return hashlib.sha256(pw + salt).hexdigest()+","+ salt

    # Validates a user login. Returns user record or None
    def validate_login(self, username, password):
        user = None
        try:
            user = self.users.find_one({'_id': username})
        except:
            print "Unable to query database for user"

        if user is None:
            print "User not in database"
            return None

        salt = user['password'].split(',')[1]

        if user['password'] != self.make_pw_hash(password, salt):
            print "user password is not a match"
            return None

        return user

    # creates a new user in the users collection
    def add_user(self, username, password, email):
        password_hash = self.make_pw_hash(password)

        user = {'_id': username, 'password': password_hash,
                'groups': ['all']}
        if email != "":
            user['email'] = email

        try:
            self.users.insert(user, safe=True)
        except pymongo.errors.OperationFailure:
            print "oops, mongo error"
            return False
        except pymongo.errors.DuplicateKeyError as e:
            print "oops, username is already taken"
            return False

        return True

    def get_user(self, username):
        return self.users.find_one({'_id':username})

    def send_msg(self, src, dst, body):
        msg = {'id': 0, 'from': src, 'body': body }
        user = self.users.find_one({'_id':dst})
        self.users.update({'_id':dst}, {'$push': {'inbox': msg}})


