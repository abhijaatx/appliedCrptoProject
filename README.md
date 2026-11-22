# Hybrid Stego-Crypto System

A small college-lab demo that encrypts a text message with AES and hides the
ciphertext in the least significant bits (LSBs) of a PNG image.

It uses OpenCV to read and write images and PyCryptodome for AES-EAX
authenticated encryption. See the usage section after setup for the commands.

This is an educational demonstration, not a secure military communication
product. LSB steganography can be detected or damaged by image processing.
