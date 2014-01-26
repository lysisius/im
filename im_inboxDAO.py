import sys
import re
import datetime
from bson.objectid import ObjectId # holy ((*^(&^&^&)))


class InboxDAO:
    def __init__(self, db, asyncdb):
        self.db = db
        self.inbox = db.inbox

        self.asyncdb = asyncdb
        self.inbox_async = asyncdb.inbox
        self.users_async = asyncdb.users

        self.inbox_cache = []


    def send(self, dst, src, body, grp=False, send_cb=None):
        # no validation on the dst, assuming the it's done before it gets here
        try:
            if grp:
                # self.grp_inbox.insert(msg)
                # TODO: this is probably the bottle neck
                # Need to figure out if an index can help
                def _cb(user_grp, error): # why error has to be spelled exactly?
                    assert not error
                    msgs = []
                    for user in user_grp:
                        msg = {
                        'dst': user['_id'],
                        'src': src,
                        'body': body,
                        'read': False,
                        'date': datetime.datetime.utcnow(),
                        'grp': dst
                        }
                        msgs.append(msg)
                    print 'inserting, ', len(msgs), 'msgs'
                    self.inbox_async.insert(msgs, callback=send_cb)
                    print '%s sends a msg to group (%s)' %(src, dst)
                # it's the limit, stupid
                self.users_async.find({'groups':dst}, limit=10**5, callback=_cb)
                # user_grp = self.users.find({'groups':dst})
                # _cb(user_grp, None)
            else:
                msg = {
                'dst': dst,
                'src': src,
                'body': body,
                'read': False,
                'date': datetime.datetime.utcnow(),
                'grp': None
                }
                self.inbox_async.insert(msg, callback=send_cb)
                # self.inbox.insert(msg)
                print '%s sends a msg to %s' %(src, dst)
        except:
            print 'error inserting the msg'
            print "Unexpected error:", sys.exc_info()[0]
            return False

        # True means successful
        return True

    def inbox_cache_cb(self, msgs, error):
        self.inbox_cache = []
        for m in msgs:
            self.inbox_cache.append(m)
        print 'updated inbox_cache, msg count:', len(self.inbox_cache)

    def get_msg(self, dst, grps):
        """
        grp is probably not going to simply be a list of strings, but
        also include the last sequence number
        """
        self.inbox_async.find({'dst': dst}, callback=self.inbox_cache_cb)
        return [m for m in self.inbox_cache if m['dst']==dst]

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








