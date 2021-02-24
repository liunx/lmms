from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class Callback:
    def demo(self):
        return 'hello world!'

callback = Callback()

# Create server
with SimpleXMLRPCServer(('localhost', 8000),
                        requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    server.register_multicall_functions()

    server.register_instance(callback)

    # Run the server's main loop
    server.serve_forever()
