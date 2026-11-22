"""AES encryption and simple LSB image steganography for a lab demo."""

import argparse
import getpass
import os
import shutil
from pathlib import Path

import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

MAGIC = b"STG1"
SALT_SIZE = NONCE_SIZE = TAG_SIZE = 16


def encrypt(message, password):
    salt = os.urandom(SALT_SIZE)
    key = PBKDF2(password.encode(), salt, dkLen=32, count=200_000)
    nonce = os.urandom(NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(message)
    return salt + nonce + tag + ciphertext


def decrypt(packet, password):
    if len(packet) < SALT_SIZE + NONCE_SIZE + TAG_SIZE:
        raise ValueError("Hidden data is incomplete.")
    salt, nonce, tag = packet[:16], packet[16:32], packet[32:48]
    key = PBKDF2(password.encode(), salt, dkLen=32, count=200_000)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    try:
        return cipher.decrypt_and_verify(packet[48:], tag)
    except ValueError as error:
        raise ValueError("Wrong passphrase or damaged image.") from error


def read_image(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def extract_packet(path):
    pixels = read_image(path).reshape(-1)
    if len(pixels) < 64:
        raise ValueError("Image is too small.")
    header = np.packbits(pixels[:64] & 1).tobytes()
    if header[:4] != MAGIC:
        raise ValueError("No message found (or image was changed).")
    size = int.from_bytes(header[4:], "big")
    if 64 + size * 8 > len(pixels):
        raise ValueError("Message is incomplete or image is too small.")
    return np.packbits(pixels[64:64 + size * 8] & 1).tobytes()


def embed(cover_path, message_path, stego_path, password):
    cover = read_image(cover_path)
    packet = encrypt(Path(message_path).read_bytes(), password)
    data = MAGIC + len(packet).to_bytes(4, "big") + packet
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    pixels = cover.reshape(-1)
    if len(bits) > len(pixels):
        raise ValueError("Message is too large for this image.")
    pixels[:len(bits)] = (pixels[:len(bits)] & 254) | bits
    stego_path = Path(stego_path)
    if stego_path.suffix.lower() != ".png":
        raise ValueError("Save the stego image as PNG to preserve its LSBs.")
    if not cv2.imwrite(str(stego_path), cover):
        raise ValueError(f"Could not save image: {stego_path}")
    backup = Path(str(stego_path) + ".cover.png")
    if not cv2.imwrite(str(backup), read_image(cover_path)):
        raise ValueError(f"Could not save cover backup: {backup}")
    print(f"Saved stego image: {stego_path}")
    print(f"Saved original cover: {backup}")


def extract(stego_path, message_path, password):
    backup = Path(str(stego_path) + ".cover.png")
    if not backup.exists():
        raise ValueError(f"Original cover backup not found: {backup}")
    message = decrypt(extract_packet(stego_path), password)
    Path(message_path).write_bytes(message)
    restored = Path(str(message_path) + ".cover.png")
    shutil.copyfile(backup, restored)
    print(f"Saved message: {message_path}")
    print(f"Restored cover: {restored}")


def assess(stego_path, password):
    stego_path = Path(stego_path)
    image = read_image(stego_path)
    decrypt(extract_packet(stego_path), password)
    folder = stego_path.parent / f"{stego_path.stem}_attacks"
    folder.mkdir(exist_ok=True)
    h, w = image.shape[:2]
    variants = {
        "JPEG compression": (folder / "compressed.jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 25]),
        "Cropping": (folder / "cropped.png", image[h // 10:, w // 10:], []),
        "PNG to BMP": (folder / "converted.bmp", image, []),
    }
    for name, (path, changed, options) in variants.items():
        if not cv2.imwrite(str(path), changed, options):
            raise ValueError(f"Could not create attack image: {path}")
        try:
            decrypt(extract_packet(path), password)
            result = "message recovered"
        except ValueError:
            result = "message damaged"
        print(f"{name}: {result} ({path})")


def pair_score(image):
    counts = np.bincount(image.reshape(-1), minlength=256).astype(float)
    even, odd = counts[::2], counts[1::2]
    return float(np.sum((even - odd) ** 2 / np.maximum(even + odd, 1)))


def analyze(stego_path):
    stego = read_image(stego_path)
    cover_path = Path(str(stego_path) + ".cover.png")
    cover = read_image(cover_path)
    if cover.shape != stego.shape:
        raise ValueError("Cover backup and stego image dimensions differ.")
    changed = np.mean((cover & 1) != (stego & 1))
    print(f"Changed LSBs: {changed:.2%}")
    print(f"Even/odd pair score (cover): {pair_score(cover):.1f}")
    print(f"Even/odd pair score (stego): {pair_score(stego):.1f}")
    print("A lower stego score can indicate LSB replacement; this is only a basic clue.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("embed", help="encrypt and hide a text file")
    add.add_argument("cover", help="cover image")
    add.add_argument("message", help="confidential text file")
    add.add_argument("stego", help="output PNG image")
    get = commands.add_parser("extract", help="extract and decrypt a message")
    get.add_argument("stego", help="stego PNG image")
    get.add_argument("message", help="output message file")
    check = commands.add_parser("assess", help="try common image transformations")
    check.add_argument("stego", help="stego PNG image")
    stats = commands.add_parser("analyze", help="compare basic LSB statistics")
    stats.add_argument("stego", help="stego PNG image")
    args = parser.parse_args()
    if args.command == "embed":
        embed(args.cover, args.message, args.stego, getpass.getpass("Passphrase: "))
    elif args.command == "extract":
        extract(args.stego, args.message, getpass.getpass("Passphrase: "))
    elif args.command == "assess":
        assess(args.stego, getpass.getpass("Passphrase: "))
    else:
        analyze(args.stego)


if __name__ == "__main__":
    main()
