# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from tests import TestCase, test
from tests.sms import SmsTestCommon


class TestSmsIncoming(TestCase, SmsTestCommon):
    def tearDown(self):
        self.marionette.execute_script("""
            SpecialPowers.removePermission("sms", document);
            SpecialPowers.setBoolPref("dom.sms.enabled", false);
        """)
        TestCase.tearDown(self)

    @test
    def test_sms_incoming(self):
        self.setup_onreceived_listener()
        self.instruct("From a different phone, send an SMS to the Firefox OS device and wait for it to arrive")
        self.verify_sms_received()
        self.remove_onreceived_listener()

        # verify text content
        self.confirm("Received SMS with text '%s'; does this text match what was sent to the Firefox OS phone?" %self.in_sms['body'])

        # verify the other message fields
        self.assertEqual(self.in_sms['type'], 'sms', "Received SMS MozSmsMessage.type should be 'sms'")
        self.assertTrue(self.in_sms['id'] > 0, "Received SMS MozSmsMessage.id should be > 0")
        self.assertTrue(self.in_sms['threadId'] > 0, "Received SMS MozSmsMessage.threadId should be > 0")
        self.assertEqual(self.in_sms['delivery'], 'received', "Received SMS MozSmsMessage.delivery should be 'received'")
        self.assertTrue((self.in_sms['deliveryStatus'] == 'success') | (self.in_sms['deliveryStatus'] == 'not-applicable'),
                        "Sent SMS MozSmsMessage.deliveryStatus should be 'success' or 'not-applicable'")
        # cannot guarantee end-user didn't read message; test that specifically in a different test
        self.assertTrue(((self.in_sms['read'] == False) or (self.in_sms['read'] == True)),
                        "Received SMS MozSmsMessage.read field should be False or True")
        # for privacy, don't print/check actual receiver (Firefox OS) phone number; just ensure not empty
        self.assertTrue(len(self.in_sms['receiver']) > 0, "Received SMS MozSmsMessage.receiver field should not be empty")
        # for privacy, don't print/check the actual sender's number; just ensure it is not empty
        self.assertTrue(len(self.in_sms['sender']) > 0, "Received SMS MozSmsMessage.sender field should not be empty")
        # timezones and different SMSC's, don't check timestamp value; just ensure non-zero
        self.assertTrue(self.in_sms['timestamp'] > 0, "Received SMS MozSmsMessage.timestamp should not be 0")
        self.assertTrue(self.in_sms['messageClass'] in ["class-0", "class-1", "class-2", "class-3", "normal"],
                        "Received SMS MozSmsMessage.messageClass must be a valid class")
