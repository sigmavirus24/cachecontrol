import requests

from mock import Mock

from cachecontrol.compat import pickle
from cachecontrol.serialize import Serializer


class TestSerializer(object):

    def setup(self):
        self.serializer = Serializer()
        self.response_data = {
            'response': {
                # Encode the body as bytes b/c it will eventually be
                # converted back into a BytesIO object.
                'body': 'Hello World'.encode('utf-8'),
                'headers': {
                    'Content-Type': 'text/plain',
                    'Expires': '87654',
                    'Cache-Control': 'public',
                },
                'status': 200,
                'version': '2',
                'reason': '',
                'strict': '',
                'decode_content': True,
            },
        }

    def test_load_by_version_one(self):
        data = b'cc=0,somedata'
        req = Mock()
        resp = self.serializer.loads(req, data)
        assert resp is None

    def test_read_version_two(self):
        req = Mock()
        resp = self.serializer._loads_v1(req, pickle.dumps(self.response_data))
        # We have to decode our urllib3 data back into a unicode
        # string.
        assert resp.data == 'Hello World'.encode('utf-8')

    def test_read_v1_serialized_with_py2_TypeError(self):
        # This tests how the code handles in reading data that was pickled
        # with an old version of cachecontrol running under Python 2
        req = Mock()
        py2_pickled_data = b"".join([
            b"(dp1\nS'response'\np2\n(dp3\nS'body'\np4\nS'Hello World'\n",
            b"p5\nsS'version'\np6\nS'2'\nsS'status'\np7\nI200\n",
            b"sS'reason'\np8\nS''\nsS'decode_content'\np9\nI01\n",
            b"sS'strict'\np10\nS''\nsS'headers'\np11\n(dp12\n",
            b"S'Content-Type'\np13\nS'text/plain'\np14\n",
            b"sS'Cache-Control'\np15\nS'public'\np16\n",
            b"sS'Expires'\np17\nS'87654'\np18\nsss."])
        resp = self.serializer._loads_v1(req, py2_pickled_data)
        # We have to decode our urllib3 data back into a unicode
        # string.
        assert resp.data == 'Hello World'.encode('utf-8')

    def test_read_version_three_streamable(self, url):
        original_resp = requests.get(url, stream=True)
        req = original_resp.request

        resp = self.serializer.loads(
            req, self.serializer.dumps(
                req,
                original_resp.raw
            )
        )

        assert resp.read()

    def test_read_version_three(self, url):
        original_resp = requests.get(url)
        data = original_resp.content
        req = original_resp.request

        resp = self.serializer.loads(
            req, self.serializer.dumps(
                req,
                original_resp.raw,
                body=data
            )
        )

        assert resp.read() == data

    def test_no_vary_header(self, url):
        original_resp = requests.get(url)
        data = original_resp.content
        req = original_resp.request

        # We make sure our response has a Vary header and that the
        # request doesn't have the header.
        original_resp.raw.headers['vary'] = 'Foo'

        assert self.serializer.loads(
            req, self.serializer.dumps(
                req,
                original_resp.raw,
                body=data
            )
        )
