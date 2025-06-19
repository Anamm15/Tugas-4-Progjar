from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer
import argparse

import concurrent

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection, address):
    rcv = b""
    MAX_REQUEST_SIZE = 10 * 1024 * 1024 

    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break

            rcv += data

            # Cari akhir dari header HTTP
            header_end = rcv.find(b"\r\n\r\n")
            if header_end != -1:
                headers_part = rcv[:header_end].decode(errors='replace')
                body_start = header_end + 4

                # Temukan Content-Length (jika ada)
                content_length = 0
                for line in headers_part.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break

                total_expected = body_start + content_length

                # Terima sisanya jika belum lengkap
                while len(rcv) < total_expected:
                    if len(rcv) > MAX_REQUEST_SIZE:
                        connection.sendall(b"HTTP/1.0 413 Payload Too Large\r\n\r\n")
                        connection.close()
                        return
                    rcv += connection.recv(1024)

                # Proses request lengkap
                request_data = rcv[:total_expected].decode(errors='replace')
                hasil = httpserver.proses(request_data)
                hasil += b"\r\n\r\n"
                connection.sendall(hasil)
                break

    except Exception as e:
        error_response = httpserver.response(500, 'Internal Server Error', str(e), {})
        connection.sendall(error_response)
    finally:
        connection.close()


class Server:
    def __init__(self, method='thread'):
        self.method = method.lower()
        self.executor_cls = concurrent.futures.ProcessPoolExecutor if self.method == 'process' else concurrent.futures.ThreadPoolExecutor

    def run(self):
        the_clients = []
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.bind(('0.0.0.0', 8885))
        my_socket.listen(1)

        with self.executor_cls(max_workers=20) as executor:
            while True:
                connection, client_address = my_socket.accept()
                logging.warning("connection from {}".format(client_address))
                p = executor.submit(ProcessTheClient, connection, client_address)
                the_clients.append(p)

                aktif = sum(1 for i in the_clients if not i.done())
                print(f"Jumlah aktif: {aktif}")

def main():
    parser = argparse.ArgumentParser(description="Flexible File Server")
    parser.add_argument("--method", choices=['thread', 'process'], default='thread',
                        help="Metode eksekusi: 'thread' atau 'process'")
    
    args = parser.parse_args()
    server = Server(args.method)
    server.run()

if __name__ == "__main__":
    main()
