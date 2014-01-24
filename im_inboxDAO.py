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
        inbox = []
        msgs = self.inbox.find({'dst': dst})
        if msgs:
            inbox += msgs
        for grp in grps:
            grp_msgs = self.grp_inbox.find({'dst': grp})
            if grp_msgs:
                inbox += grp_msgs
        return inbox

    def del_msg(self, msgid):
        print 'hey there'
        print ObjectId(msgid)
        try:
            self.inbox.remove({'_id':ObjectId(msgid)})
        except:
            print 'error deleting the msg with id %s' % msgid
            print "Unexpected error:", sys.exc_info()[0]
        return


    def read(self, msgid):
        """
        mark the message as read
        """
        pass








