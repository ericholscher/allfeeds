from django.test.client import Client
from django.test.testcases import TestCase
from socialgraph.models import Request

from mock import Mock
import urllib2
import yaml

class TestInput(TestCase):
    """
    Test the input functions from getting things from google
    """

    def setUp(self):
        import test_data
        #Get our relationships
        resp_mock = Mock()
        resp_mock.read.return_value = test_data.ericholscher
        urllib2.urlopen = Mock()
        urllib2.urlopen.return_value = resp_mock

    def test_load_data(self):
        test_url = 'http://twitter.com/ericholscher'
        eric = Request(url=test_url)
        self.assertEqual(urllib2.urlopen.called, False)
        eric.populate_structure()
        self.assertEqual(urllib2.urlopen.called, True)
        self.assertEqual(len(eric.claimed), 27)
        self.assertEqual(len(eric.referenced), 122)

    def test_relationship_reciprical(self):
        pass
