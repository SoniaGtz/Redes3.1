HOST, PORT = "50.0.0.2", 1500
import logging
import socketserver
import time
from NetFlow import ExportPacket, TemplateNotRecognized

#Comportamiento del servidor UDP
class NetflowUDPHandler(socketserver.BaseRequestHandler):
    templates = {}
    buffered = {}

    def handle(self):
        data = self.request[0]
        host = self.client_address[0]
        export = None
        try:
            export = ExportPacket(data, self.templates)
        except TemplateNotRecognized:
            self.buffered[time.time()] = data
            print("Received data with unknown template, data stored in buffer!")

            return



if __name__ == "__main__":
    try:
        server = socketserver.UDPServer((HOST, PORT), NetflowUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")