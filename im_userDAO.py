import hmac
import random
import string
import hashlib
import pymongo

class UserDAO:
    def __init__(self, db):
        self.db = db
        self.users = self.db.users
        # self.users_cache = {}
        self.groups = self.db.groups
        self.groups_cache = []
        print 'DB read: groups'
        for group in self.groups.find():
            self.groups_cache.append(group)
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

        # all is the default group where everybody is in
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
        """
        TODO: error checking
        """
        return self.users.find_one({'_id':username})


    def join_group(self, username, group):
        """
        the UI should ensure that the error cases don't happen.
        so maybe the logic can be simplied. 
        """
        # if user already part of the group
        user = self.get_user(username)
        if group in user['groups']:
            print 'already a member'
            return False
        # if group doesn't exist
        if not self.groups.find_one({'_id':group}):
            print 'the group does not exist'
            return False

        # add the group into the user record
        try:
            self.users.update({'_id':username}, {'$push': {'groups': group}})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            return False
        return True

    def leave_group(self, username, group):
        user = self.get_user(username)
        if group not in user['groups']:
            print 'user not in this group'
            return False

        # remove the group from the user record
        try:
            self.users.update({'_id':username}, {'$pull': {'groups': group}})
        except:
            print "Unexpected error:", sys.exc_info()[0]
            return False
        return True


    def get_groups(self):
        """
        return all the groups
        TODO: error checking
        """
        return self.groups_cache

    def get_groups_membership(self, username):
        """
        return all the groups and indicate the membership of the user
        """
        user = self.get_user(username)
        user_groups = user['groups']
        all_groups = self.get_groups()
        # print [(group, group in user_groups) for group in all_groups]
        return [(group['_id'], group['_id'] in user_groups) for group in all_groups]




