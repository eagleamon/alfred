from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.web import HTTPError
import tornado.gen
import logging

defaultConfig = {
    "http": {
        "weather": {
            "url": "http://www.google.be",
            "timeout": 5,
            "regex": ".*",
            "refresh": "*/30"
        }
    }
}

log = logging.getLogger(__name__)


def setup(alfred):
    config = alfred.get_config(__name__)
    for loop in config:
        alfred.schedule(
            __name__, update, loop, config[loop].get('refresh', "*/30"))


def stop(alfred):
    alfred.deschedule(__name__)


@tornado.gen.coroutine
def update(alfred, data):
    config = alfred.get_config(__name__)[data]

    for item in alfred.activeItems.get('http'):
        if item.binding.split(':')[1] == data:
            req = HTTPRequest(url = config.get('url', ''), connect_timeout=config.get('timeout', 20),
                            request_timeout = config.get('timeout', 20))
            hc = AsyncHTTPClient()
            log.debug('Fetching %s' % req.url)

            # Yield the Future
            res = yield hc.fetch(req)
            if res.error:
                raise HTTPError(res)
            item.value = res.body.decode().strip()
