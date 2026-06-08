import socket
import struct
import numpy as np
import sounddevice as sd

PORT = 58710
TARGET_ID = b"hifi"

# 🔥 FORCE REAL OUTPUT DEVICE (your Pi headphone jack)
DEVICE = 0  # bcm2835 Headphones

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
except Exception:
    pass

sock.bind(("0.0.0.0", PORT))

stream = None

print(f"Listening for ReaStream target ID: {TARGET_ID.decode()}")

while True:
    data, _ = sock.recvfrom(65535)

    if len(data) < 47:
        continue

    if data[0:4] != b"MRSR":
        continue

    packet_size = struct.unpack("<I", data[4:8])[0]

    ident = data[8:40].split(b"\x00")[0]
    if ident != TARGET_ID:
        continue

    nch = data[40]
    samplerate = struct.unpack("<I", data[41:45])[0]
    sblocklen = struct.unpack("<H", data[45:47])[0]

    audio_bytes = data[47:47 + sblocklen]

    samples = np.frombuffer(audio_bytes, dtype=np.float32)

    if nch > 1:
        frames = len(samples) // nch
        samples = samples.reshape(nch, frames).T
    else:
        samples = samples.reshape(-1, 1)

    samples = np.ascontiguousarray(samples)

    # 🔥 FIX: initialize stream with explicit device
    if stream is None:
        print(f"Starting audio stream @ {samplerate} Hz, {nch} ch, device {DEVICE}")

        stream = sd.OutputStream(
            device=DEVICE,          # <<< THIS WAS MISSING
            samplerate=48000,
            channels=nch,
            dtype="float32",
            latency="high",
            blocksize=1024
        )
        stream.start()

    try:
        stream.write(samples)
    except Exception as e:
        print("audio write error:", e)
