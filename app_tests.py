import os
import app
import unittest
import tempfile

class HomeTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        #app.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])
	

    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'Concept Land Registry Digital Services' in rv.data

if __name__ == '__main__':
    unittest.main()

    
