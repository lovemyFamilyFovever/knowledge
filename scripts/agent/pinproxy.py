"""Localhost-only CONNECT tunnel that pins github.com:443 to a reachable edge IP.

TLS stays end-to-end: we only forward bytes, we never terminate or inspect them,
so git still validates the real github.com certificate. Nothing is written to
system config; kill this process and the route is gone.
"""
import os
import socket
import sys
import threading

PINS = {("github.com", 443): os.environ.get("KB_GH_IP", "140.82.113.3")}
LISTEN = ("127.0.0.1", int(os.environ.get("KB_PIN_PORT", "18080")))


def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def handle(conn, addr):
    try:
        conn.settimeout(20)
        req = conn.recv(4096).decode("latin-1")
        verb, target = req.split("\r\n")[0].split()[0:2]
        host, _, port = target.rpartition(":")
        if verb != "CONNECT":
            conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            return
        pin = PINS.get((host, int(port or 443)))
        if pin is None:
            # only the pinned host is allowed through this tunnel
            conn.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            print("DENY %s" % target, flush=True)
            return
        upstream = socket.create_connection((pin, int(port or 443)), timeout=20)
        conn.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        print("TUNNEL %s -> %s" % (target, pin), flush=True)
        t = threading.Thread(target=pipe, args=(upstream, conn), daemon=True)
        t.start()
        pipe(conn, upstream)
        t.join(5)
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        print("ERR %s" % exc, flush=True)
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(LISTEN)
    srv.listen(16)
    print("LISTENING %s:%d pin=%s pid=%d" % (*LISTEN, PINS[("github.com", 443)], os.getpid()), flush=True)
    sys.stdout.flush()
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
