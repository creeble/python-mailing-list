#!/usr/bin/python3

import sys
import email
import email.utils
import logging
import smtplib
from email.message import EmailMessage
# just for the attachment in a rejected message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re

# required
LIST_NAME = sys.argv[1].lower()		# listname@domain.com
LIST_DIR = sys.argv[2]			# where to find the recipient/sender/listname files
# optional, appears in procmail.log typically if None
LOG_FILE_PATH = None
# don't log at all
LOGGING = False

if len(sys.argv) > 3:
        LOGGING = True
        LOG_FILE_PATH = sys.argv[3]


# List name is taken from To: address; i.e., peeps@DOMAIN == peeps
# LIST_DIR/peeps.senders are allowed senders
# LIST_DIR/peeps.recipients is the list
# LIST_DIR/peeps.listname is a two-line file:
#   line 1 is a list name, which gets prepended to the subject [In Braces]
#   line 2 is the administrator's email address, which is used for bounces

LOGGING and logging.basicConfig(filename=LOG_FILE_PATH, level=logging.DEBUG)

# debugging
#with open('msg.txt') as x: full_msg = x.read()
full_msg = sys.stdin.read()
msg = email.message_from_string(full_msg)
#logging.info(full_msg)

name,addr = email.utils.parseaddr(LIST_NAME)
logging.info("From:  " + msg['from'])
logging.info("Subject: " + msg['subject'])
logging.info("To: " + msg['to'])
logging.info("List: " + LIST_NAME)

List_address, Domain = [a.lower() for a in addr.split("@")]

def get_allowed():
        with open(LIST_DIR + '/' + List_address + '.senders') as f:
                allowed = f.readlines()
        ret = [email.utils.parseaddr(x) for x in allowed]
        return [x[1] for x in ret]

def not_allowed(address, admin, msg):
        m = MIMEMultipart()
        m['to']   = address
        m['from'] = admin
        m['Subject'] = "Message rejected - not an allowed sender"
        message = "Your message could not be delivered.\n\n"
        message += "You must be an authorized sender for the {} list.\n".format(addr)
        m.attach(MIMEText(message, "plain"))
        # Include the sent message as an attachment.
        part = MIMEBase('text', 'rfc822')
        part.set_payload(msg.as_string())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment')
        m.attach(part)
        s = smtplib.SMTP('localhost')
        s.send_message(m)
        s.quit

def get_recipients():
        with open(LIST_DIR + '/' + List_address + '.recipients') as f:
                recipients = f.readlines()
        # This kills EOL and puts everything in a list of single strings.
        return [email.utils.formataddr(x) for x in [email.utils.parseaddr(y) for y in recipients]]

def get_listname():
        with open(LIST_DIR + '/' + List_address + '.listname') as f:
                lname = f.readlines()
        # [list name] in subject, admin address
        return [lname[0].strip(), lname[1].strip()]


allowed = get_allowed()
listname, admin = get_listname()

mfrom = email.utils.parseaddr(msg['from'])[1].lower()
if mfrom not in allowed:
        not_allowed(msg['from'], admin, msg)
        exit()

recipients = get_recipients()

# create a normalized list of "to" addresses, including
# cc and bcc, as a "reject" list for recipients (since they're already
# getting the message).  This is mostly so that a "reply all" doesn't
# create an annoying duplicate message.
# Note that the following lines would fail if it weren't for the fact that
# is *always* a 'to' address...
all_to = email.utils.getaddresses(msg.get_all('to', []) + msg.get_all('cc', []) + msg.get_all('bcc', []))
reject = set([x[1].lower() for x in all_to if x[1].lower() != addr])

# fixup subject - critical to delete first! (yahoo.com in particular doesn't like two)
s = msg['Subject']
m = re.search("\[{}\]".format(listname), s)
if not m:
        del msg['Subject']
        msg['Subject'] = '[' + listname + '] ' + s

# also to: name / address
# Gmail displays this by parsing a "first name" from the list name, but whatever.
del msg['to']
msg['to'] = '"{}" <{}@{}>'.format(listname, List_address, Domain)

# It is probably good to delete this header, as it will be incorrect
# after forwarding, and the forwarder *should* create its own DKIM
# signature.
# Note that some mailers will create the WRONG DKIM signature, using
# the original domain rather than the mailing list domain.  Not much
# can be done about that here.
del msg['DKIM-Signature'];

for r in recipients:
        # don't send if in reject list
        n, a = email.utils.parseaddr(r)
        if a.lower() in reject:
                next
        # send it
        s = smtplib.SMTP('localhost')
        # Tell the receiving MTA that the message is coming from the
        # the list address, not the original sender.  This avoids some
        # level of spam blocking.
        s.send_message(msg, from_addr=msg['to'], to_addrs=r)
        s.quit
