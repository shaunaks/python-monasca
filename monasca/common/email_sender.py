# Copyright 2015 Carnegie Mellon University
#
# Author: Han Chen <hanc@andrew.cmu.edu>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import email.mime.text
import smtplib

from monasca.openstack.common import log

LOG = log.getLogger(__name__)


class EmailSender(object):
    """Send emails to notify user."""
    mail_username = 'monasca.notification@gmail.com'
    mail_password = 'notification'
    HOST = 'smtp.gmail.com'
    PORT = 25
    from_addr = mail_username
    smtp = None

    def __init__(self):
        self.smtp = smtplib.SMTP()
        # show the debug log
        self.smtp.set_debuglevel(1)

        LOG.debug('connecting ...')

        # connect
        try:
            self.smtp.connect(self.HOST, self.PORT)
        except Exception:
            LOG.debug('SMTP Connection error.')

        # gmail uses ssl
        self.smtp.starttls()
        # login with username & password
        try:
            LOG.debug('Login ...')
            self.smtp.login(self.mail_username, self.mail_password)
        except Exception:
            LOG.debug('Login exception.')

    def reset(self):
        self.__init__()

    def send_emails(self, to_addrs, subject, content):
        # fill content with MIMEText's object
        msg = email.mime.text.MIMEText(content)
        msg['From'] = self.from_addr
        msg['To'] = ';'.join(to_addrs)
        msg['Subject'] = subject
        try:
            self.smtp.sendmail(self.from_addr, to_addrs, msg.as_string())
            LOG.debug('Mail sent to: %s' % str(to_addrs))
            return True
        except Exception as e:
            LOG.debug('Mail sent Exception: %s, reset the sender.' % str(e))
            self.smtp.quit()
            self.reset()
            return False
