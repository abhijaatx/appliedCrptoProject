# Hybrid Stego-Crypto System

A college-lab command-line demo that encrypts a text file with AES and hides
the encrypted bytes in the least significant bits (LSBs) of a PNG image.
OpenCV handles images; PyCryptodome provides AES-EAX.

## Requirements and setup

- Python 3
- A cover image, such as `cover.png`
- A plain-text message file, such as `message.txt`

Install the Python packages:

```bash
python -m pip install -r requirements.txt
```

## Run

From this project directory, embed a message and then extract it:

```bash
python stego.py embed cover.png message.txt stego.png
python stego.py extract stego.png recovered.txt
```

Each command prompts for a passphrase. Use the same passphrase for extraction.
The passphrase is not saved or embedded in the image.

### Expected behavior

Embedding encrypts the bytes from `message.txt`, adds a short marker and length
header, then stores the packet in the color-channel LSBs. It creates:

- `stego.png` — the image carrying the encrypted packet
- `stego.png.cover.png` — a lossless copy of the decoded cover image

Extraction verifies and decrypts the packet, then creates:

- `recovered.txt` — the original message bytes
- `recovered.txt.cover.png` — the cover-image copy from the sidecar

The sidecar is needed to restore the cover. The program does not reconstruct
the original image from the stego image alone. Save the stego image as PNG;
JPEG compression can damage its LSB data. A wrong passphrase or damaged packet
fails AES-EAX authentication instead of returning altered plaintext.

Example terminal output:

```text
$ python stego.py embed cover.png message.txt stego.png
Passphrase:
Saved stego image: stego.png
Saved original cover: stego.png.cover.png

$ python stego.py extract stego.png recovered.txt
Passphrase:
Saved message: recovered.txt
Restored cover: recovered.txt.cover.png
```

This project has a terminal interface and no graphical screen to capture; the
example above shows the normal interaction.

## Attack and steganalysis demo

Try common transformations and compare basic LSB statistics:

```bash
python stego.py assess stego.png
python stego.py analyze stego.png
```

`assess` writes JPEG-compressed, cropped, and BMP-converted images into a
`stego_attacks/` folder, then reports whether each packet still authenticates.
Lossless BMP conversion should preserve the message. Cropping or lossy JPEG
compression can damage it.

`analyze` reports the percentage of changed cover LSBs and an even/odd
pixel-pair score for the cover and stego images. LSB replacement can make
even/odd value counts more similar, which can be a clue to hidden data. This
simple statistic is not a full steganalysis detector, and AES encryption does
not make the image undetectable. A stronger evaluation would use established
methods such as RS analysis across a larger image set.

## How it works

1. PBKDF2 derives a 256-bit key from the passphrase and a random salt.
2. AES-EAX encrypts and authenticates the message using a random nonce.
3. The program writes a 64-bit header and the encrypted packet into image LSBs.
4. Extraction reads the packet and AES-EAX verifies it before releasing the
   plaintext.

The cover must have enough color-channel values for the header and packet.
Use a larger image for a larger message.

## Limitations

This is a teaching demo, not a secure military communication product. LSB
steganography can be detected by statistical analysis and damaged by image
processing. Do not use it for real confidential data.
