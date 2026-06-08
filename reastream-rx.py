import socket
import struct
import numpy as np
import sounddevice as sd

PORT = 58710
TARGET_ID = b"test"   # must match ReaStream name exactly

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  # ipv6
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # ipv4
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
except Exception:
    pass

sock.bind(("::", PORT))           # ipv6 support (reaper official plugin reastream dosen't support ipv6 yet !)
# sock.bind(("0.0.0.0", PORT))    # ipv4 support
stream = None

print(f"Listening for ReaStream target ID: {TARGET_ID.decode()}")

while True:
    data, _ = sock.recvfrom(65535)

    if len(data) < 47:
        continue

    # --- header check ---
    if data[0:4] != b"MRSR":
        continue

    packet_size = struct.unpack("<I", data[4:8])[0]

    ident = data[8:40].split(b"\x00")[0]
    if ident != TARGET_ID:
        continue

    nch = data[40]
    samplerate = struct.unpack("<I", data[41:45])[0]
    sblocklen = struct.unpack("<H", data[45:47])[0]

    # --- audio payload ---
    audio_bytes = data[47:47 + sblocklen]

    samples = np.frombuffer(audio_bytes, dtype=np.float32)

    # ReaStream = NON-interleaved channels
    if nch > 1:
        frames = len(samples) // nch
        samples = samples.reshape(nch, frames).T
    else:
        samples = samples.reshape(-1, 1)

    # 🔥 FIX: ensure memory layout is valid for sounddevice
    samples = np.ascontiguousarray(samples)

    # --- init audio stream once we know format ---
    if stream is None:
        stream = sd.OutputStream(
            samplerate=samplerate,
            channels=nch,
            dtype="float32",
            latency="low"
        )
        stream.start()

    try:
        stream.write(samples)
    except Exception as e:
        print("audio write error:", e)
