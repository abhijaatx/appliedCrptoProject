# Hybrid Stego-Crypto System

A small college-lab demo that encrypts a text message with AES and hides the
ciphertext in the least significant bits (LSBs) of a PNG image.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Use

Put the confidential message in a text file, then run:

```bash
python stego.py embed cover.png message.txt stego.png
python stego.py extract stego.png recovered.txt
```

Both commands prompt for a passphrase. Embedding creates `stego.png` and
`stego.png.cover.png`. Extraction writes `recovered.txt` and
`recovered.txt.cover.png`.

The program derives an AES-256 key from the passphrase using PBKDF2 and a
random salt. AES-EAX encrypts the message and checks its integrity. It stores a
short marker and packet length in the image, then writes packet bits into the
image's color-channel LSBs. Save the stego image as PNG because JPEG is lossy.

## Required evaluation

Run the transformations and basic LSB comparison with:

```bash
python stego.py assess stego.png
python stego.py analyze stego.png
```

`assess` creates JPEG-compressed, cropped, and BMP-converted copies, then
reports whether the encrypted message still authenticates. BMP conversion is
lossless and should preserve the message; lossy JPEG compression and cropping
can damage it. AES-EAX reports a damaged message instead of returning altered
plaintext.

`analyze` compares the cover and stego images' changed-LSB percentage and an
even/odd pixel-pair score. LSB replacement can make even/odd value counts more
similar, which can be a clue to hidden data. This simple score is not a full
steganalysis detector, and AES encryption does not make the image
undetectable. More testing, such as RS analysis on multiple images, is needed
for a serious steganalysis evaluation.

## Notes

- The original decoded cover pixels are saved losslessly in the `.cover.png`
  sidecar. The extractor copies that file back; it does not reconstruct the
  original cover from the stego image alone.
- The image must have enough color-channel values to hold the 64-bit header and
  encrypted packet. Very large messages need a larger cover image.
- This is a teaching demo, not a secure military communication product. Do not
  use it for real confidential data.
