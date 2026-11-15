"""Google OIDC write authorization must fail closed, without Secrets."""
import unittest
from time import time
from advisor_auth import is_verified_owner

class OwnerIdentityTests(unittest.TestCase):
    def setUp(self):
        self.now=int(time())
        self.identity={"is_logged_in":True,"iss":"https://accounts.google.com",
                       "email":"me@example.com","email_verified":True,
                       "exp":self.now+3600}
    def test_verified_owner(self):
        self.assertTrue(is_verified_owner(self.identity,"me@example.com",self.now))
        self.assertTrue(is_verified_owner(self.identity,"ME@example.com",self.now))
    def test_wrong_identity_or_no_owner(self):
        self.assertFalse(is_verified_owner(self.identity,"other@example.com",self.now))
        self.assertFalse(is_verified_owner(self.identity,"",self.now))
        self.assertFalse(is_verified_owner({}, "me@example.com",self.now))
        self.assertFalse(is_verified_owner(None,"me@example.com",self.now))
    def test_wrong_provider(self):
        p={**self.identity,"iss":"https://example.com"}
        self.assertFalse(is_verified_owner(p,"me@example.com",self.now))
    def test_unverified_mail(self):
        self.assertFalse(is_verified_owner({**self.identity,"email_verified":False},
                                           "me@example.com",self.now))
    def test_invalid_expiration(self):
        for exp in (None,"invalid",self.now-1,self.now+20):
            self.assertFalse(is_verified_owner({**self.identity,"exp":exp},
                                               "me@example.com",self.now))
    def test_not_authenticated(self):
        self.assertFalse(is_verified_owner({**self.identity,"is_logged_in":False},
                                           "me@example.com",self.now))
if __name__=="__main__":unittest.main()
