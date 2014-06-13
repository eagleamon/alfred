from tornado.testing import AsyncHTTPTestCase, AsyncHTTPClient, AsyncTestCase


class TestHandlerBase(AsyncTestCase):
    def setUp(self):
        super(TestHandlerBase, self).setUp()
        self.client = AsyncHTTPClient(self.io_loop)


    def tearDown(self):
        pass

    def testgetItems(self):
        res = self.client.fetch('ok')
        self.wait()
        assert res.code == 412


    def get_app(self):
        import alfred.webserver
        return alfred.webserver.WebServer().start()
