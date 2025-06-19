import sys
import os
import os.path
import uuid
from glob import glob
from datetime import datetime
from urllib.parse import unquote, urlparse, parse_qs

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
    
        # Jika messagebody adalah string, ubah ke bytes
        if type(messagebody) is not bytes:
            messagebody = messagebody.encode()
    
        resp = []
        resp.append(f"HTTP/1.0 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        for kk in headers:
            resp.append(f"{kk}: {headers[kk]}\r\n")
        resp.append("\r\n")
    
        # Gabungkan semua header menjadi satu string, lalu encode
        response_headers = "".join(resp).encode()
    
        # Gabungkan dengan body yang sudah dalam bentuk bytes
        response = response_headers + messagebody
        return response

    def proses(self, data):
        try:
            requests = data.split("\r\n")
            baris = requests[0]
            all_headers = [n for n in requests[1:] if n != '']
            j = baris.split(" ")
            method = j[0].upper().strip()
            object_address = j[1].strip()
            if method == 'GET':
                return self.http_get(object_address, all_headers)
            elif method == 'POST':
                body = data.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in data else ""
                return self.http_post(object_address, all_headers, body)
            elif method == "DELETE":
                body = data.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in data else ""
                return self.http_delete(object_address, all_headers)
            else:
                return self.response(400, 'Bad Request', '', {})
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e), {})

    def http_get(self, object_address, headers):
        # GET /
        if object_address == '/':
            return self.response(200, 'OK', 'Selamat datang di Web Server!', {
                'Content-type': 'text/plain'
            })

        elif object_address == '/files':
            if not os.path.exists('./files'):
                os.makedirs('./files')
            daftar_file = os.listdir('./files')
            isi = "Daftar File di /files:\n"
            count = 1
            for f in daftar_file:
                isi += f'{count}: {f}\n'
                count += 1
            return self.response(200, 'OK', isi, {
                'Content-type': 'text/html'
            })

        elif object_address.startswith('/files/'):
            filename = object_address[len('/files/'):]

            # Cegah path traversal (misalnya: /files/../secret.txt)
            if '..' in filename or '/' in filename or '\\' in filename:
                return self.response(403, 'Forbidden', 'Akses tidak diizinkan.', {})

            filepath = os.path.join('./files', filename)
            if not os.path.exists(filepath):
                return self.response(404, 'Not Found', 'File tidak ditemukan.', {})
            if os.path.isdir(filepath):
                return self.response(403, 'Forbidden', 'Path adalah direktori, bukan file.', {})

            ext = os.path.splitext(filepath)[1]
            ctype = self.types.get(ext, 'application/octet-stream')
            with open(filepath, 'rb') as f:
                isi = f.read()
            return self.response(200, 'OK', isi, {'Content-type': ctype})

        # Endpoint tidak dikenali
        return self.response(404, 'Not Found', 'Endpoint tidak ditemukan.', {})

    def http_post(self, object_address, headers, body):
        if object_address == '/upload':
            boundary = ''
            for h in headers:
                if h.lower().startswith("content-type:") and "boundary=" in h:
                    boundary = h.split("boundary=")[-1].strip()
                    break

            if not boundary:
                return self.response(400, 'Bad Request', 'Boundary tidak ditemukan.', {})

            boundary_bytes = ('--' + boundary).encode()

            # Pisahkan body berdasarkan boundary
            parts = body.encode(errors='replace').split(boundary_bytes)

            for part in parts:
                if b'Content-Disposition' in part:
                    header_body_split = part.split(b'\r\n\r\n', 1)
                    if len(header_body_split) != 2:
                        continue

                    headers_part = header_body_split[0].decode(errors='replace')
                    content_part = header_body_split[1].rstrip(b'\r\n--')

                    filename = ''
                    for line in headers_part.split('\r\n'):
                        if 'filename=' in line:
                            filename = line.split('filename=')[1].split(';')[0].strip('"')
                            break

                    if filename:
                        # Cegah path traversal
                        if '..' in filename or '/' in filename or '\\' in filename:
                            return self.response(400, 'Bad Request', 'Nama file tidak valid.', {})

                        os.makedirs('./files', exist_ok=True)
                        filepath = os.path.join('./files', filename)
                        with open(filepath, 'wb') as f:
                            f.write(content_part)

                        return self.response(200, 'OK', f'File {filename} berhasil diunggah.', {})

            return self.response(400, 'Bad Request', 'Gagal mengunggah file.', {})

        return self.response(404, 'Not Found', 'Endpoint POST tidak ditemukan.', {})

    def http_delete(self, object_address, headers):
        query = urlparse(object_address).query
        params = parse_qs(query)
        filename = params.get('filename', [None])[0]
        if filename:
            filepath = './files/' + filename
            if os.path.exists(filepath):
                os.remove(filepath)
                return self.response(200, 'OK', f'File {filename} berhasil dihapus.', {})
            else:
                return self.response(404, 'Not Found', 'File tidak ditemukan.', {})
        return self.response(400, 'Bad Request', 'Parameter filename tidak valid.', {})
			 	
#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)
