import os
import app
import unittest
import tempfile
import mock

class HomeTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()
        #app.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    @mock.patch('requests.get')
    def test_property(self, get_mock):
        class MockResponse(object):
            status_code = 200
            def json(self):
                return {
                "title": {
                    "title_number": "AB1234",
                    "address": "123 Fake St",
                    "registered_owners": [
                        {
                            "name": "Victor"
                        }
                    ],
                    "extent": {
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": [
                                [
                                    [
                                        [
                                            14708.755563011973,
                                            6761018.225448865
                                        ]
                                    ]
                                ]
                            ]
                        }
                    },
                    "related_titles": [
                        {
                            "title_number": "DN1234"
                        },
                        {
                            "title_number": "DN2345"
                        },
                        {
                            "title_number": "DN3456"
                        }
                    ]
                }
            }
        get_mock.return_value = MockResponse()
        rv = self.app.get('/properties/EX1354')
        assert 'Property' in rv.data
        assert '123 Fake St' in rv.data

    @mock.patch('requests.get')
    def test_property_not_found(self, get_mock):
        class MockResponse(object):
            status_code = 404
            def json(self):
                return
        get_mock.return_value = MockResponse()
        rv = self.app.get('/properties/EX1354')
        assert 'Not Found' in rv.data


    def test_properties(self):
        rv = self.app.get('/properties')
        assert 'not supported' in rv.data


if __name__ == '__main__':
    unittest.main()
