import sys
import re
import datetime
from bson.objectid import ObjectId # holy ((*^(&^&^&)))


class InboxDAO:
    def __init__(self, database):
        self.db = database
        self.inbox = database.inbox
        self.users = database.users

    def send(self, dst, src, body, grp=False):
        # no validation on the dst, assuming the it's done before it gets here
        try:
            if grp:
                # self.grp_inbox.insert(msg)
                user_grp = self.users.find({'groups':dst})
                print user_grp
                for user in user_grp:
                    print user['_id']
                    msg = {
                    'dst': user['_id'],
                    'src': src,
                    'body': body,
                    'read': False,
                    'date': datetime.datetime.utcnow(),
                    'grp': dst
                    }
                    self.inbox.insert(msg)
                print '%s sends a msg to group (%s)' %(src, dst)
            else:
                msg = {
                'dst': dst,
                'src': src,
                'body': body,
                'read': False,
                'date': datetime.datetime.utcnow(),
                'grp': None
                }
                self.inbox.insert(msg)
                print '%s sends a msg to %s' %(src, dst)
        except:
            print 'error inserting the msg'
            print "Unexpected error:", sys.exc_info()[0]
            return False

        # True means successful
        return True

    def get_msg(self, dst, grps):
        """
        grp is probably not going to simply be a list of strings, but
        also include the last sequence number
        """
        return self.inbox.find({'dst': dst})

    def del_msg(self, msgid):
        try:
            self.inbox.remove({'_id':ObjectId(msgid)})
        except:
            print 'error deleting the msg with id %s' % msgid
            print "Unexpected error:", sys.exc_info()[0]


    def read_msg(self, msgid):
        """
        mark the message as read
        """
        try:
            self.inbox.update({'_id':ObjectId(msgid)}, 
                              {'$set': {'read': True}})
        except:
            print 'error deleting the msg with id %s' % msgid
            print "Unexpected error:", sys.exc_info()[0]








