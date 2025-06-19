import socket
import os
import mimetypes

def send_request(request_bytes, host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        client_socket.sendall(request_bytes)

        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data
        return response
    finally:
        client_socket.close()

def http_get_file(host, port, path):
    request = f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    response = send_request(request.encode(), host, port)

    header_end = response.find(b"\r\n\r\n")
    if header_end == -1:
        print("❌ Response tidak valid.")
        return

    headers = response[:header_end].decode(errors='replace')
    body = response[header_end + 4:]

    print("📥 GET Response Header:")
    print(headers)
    print("==============================")

    content_type = ''
    for line in headers.split("\r\n"):
        if line.lower().startswith("content-type"):
            content_type = line.split(":", 1)[1].strip()

    if content_type.startswith("application/") or content_type.startswith("image/"):
        filename = os.path.basename(path)
        with open(filename, "wb") as f:
            f.write(body)
        print(f"✅ File berhasil disimpan sebagai '{filename}'")
    else:
        print("📝 Isi:")
        print(body.decode(errors='replace'))

def http_post_file(host, port, path, file_path):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

    with open(file_path, 'rb') as f:
        file_content = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    request = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body

    response = send_request(request, host, port)
    print("📤 POST Response:")
    print(response.decode(errors='replace'))

def http_delete_file(host, port, filename):
    path = f"/files?filename={filename}"
    request = (
        f"DELETE {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n\r\n"
    )
    response = send_request(request.encode(), host, port)
    print("🗑️ DELETE Response:")
    print(response.decode(errors='replace'))

if __name__ == "__main__":
    host = "172.16.16.101"
    port = 8885

    # === GET file dari server dan simpan lokal
    # http_get_file(host, port, "files/donalbebek.jpg")
    # http_get_file(host, port, "files/contoh.pdf")

    # === Upload file ke server
    #http_post_file(host, port, "/upload", "pokijan.jpg")
    #http_post_file(host, port, "/upload", "contoh.jpg")

    # === Hapus file dari server (gunakan nama file yang ada)
    # http_delete_file(host, port, "pokijan.jpg")
