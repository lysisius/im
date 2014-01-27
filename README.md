im
==

a web based messaging app that does:
- signup and login
- sending and receiving messages
- groups and membership
- group messages
- deleting messages

findings:
- by using asyncmongo to handle sending group messages, the response time decreased drastically. in the synchronous case, a message for 10k users would cause 1500ms delay to insert, with asyncmongo, 6ms
- caching the inbox also helps by reducing the response delay from 200ms to 20ms

database - MongoDB; web server - Tornado
database driver - pymongo and asyncmongo


