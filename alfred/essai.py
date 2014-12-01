import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

if __name__ == "__main__":
    print('ok')
    # application = tornado.web.Application([
    #     (r"/", MainHandler),
    # ], debug=True)
    # application.listen(8888)
    # tornado.ioloop.IOLoop.instance().start()
