import socket
import struct
import numpy as np
import sounddevice as sd

# ---------------- CONFIG ----------------
# Network
IP = "0.0.0.0"        # change if sending over network
PORT = 58710            # default reastream port
TARGET_ID = b"test"     # must match receiver exactly

# Audio
CHANNELS = 2            # up to 64 channels per target_id
SAMPLERATE = 48000
BLOCKSIZE = 1024        # frames per UDP packet (keep small for stability)
# ----------------------------------------

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

def build_packet(audio_block: np.ndarray):
    """
    audio_block shape: (frames, channels), dtype float32
    ReaStream expects NON-interleaved -> (channels, frames)
    """

    # convert to non-interleaved
    if audio_block.ndim == 1:
        audio_block = audio_block[:, None]

    audio_block = audio_block.astype(np.float32, copy=False)
    non_interleaved = audio_block.T  # (ch, frames)

    payload = non_interleaved.tobytes()

    nch = non_interleaved.shape[0]
    samplerate = SAMPLERATE
    sblocklen = len(payload)

    header = b"MRSR"

    # ident padded to 32 bytes
    ident = TARGET_ID.ljust(32, b"\x00")

    packet_size = 47 + sblocklen

    packet = (
        header +
        struct.pack("<I", packet_size) +
        ident +
        struct.pack("<B", nch) +
        struct.pack("<I", samplerate) +
        struct.pack("<H", sblocklen) +
        payload
    )

    return packet


def callback(indata, frames, time, status):
    if status:
        print(status)

    packet = build_packet(indata)
    sock.sendto(packet, (IP, PORT))


print(f"Sending ReaStream audio to {IP}:{PORT} as '{TARGET_ID.decode()}'")

with sd.InputStream(
    samplerate=SAMPLERATE,
    channels=CHANNELS,
    dtype="float32",
    blocksize=BLOCKSIZE,
    callback=callback
):
    print("Streaming... Press Ctrl+C to stop.")
    while True:
        sd.sleep(1000)
