# CS-4463 Final Project — Team 11

**Nearest Luminance Palette Hiding Technique**

Micheal Chandler, William Penrose, Kiahna Isadore

Hides and extracts messages in **8-bit paletted** images.

## Setup

Requires the Pillow library: `pip install pillow`

## Usage

### No parameters

Running with no arguments prints a short usage reminder:

```bash
python finalproject.py
```

```
Please specify either -hide or -extract. Use -h for help.
```

### Help menu

```bash
python finalproject.py -h
```

### Hide a message

```bash
python finalproject.py -hide -m <message_file> -c <cover_file> [-o <stego_file>] [--bits N]
```

**Arguments**

- `-m` : Message file to hide, or `random` for random bits
- `-c` : Cover image 
- `-o` : Output stego image (optional)
- `--bits` : Bits hidden per pixel, 1–8 (optional; default: `1`)

### Extract a message

```bash
python finalproject.py -extract -s <stego_file> [-o <output_file>] [--bits N]
```

**Arguments**

- `-s` : Stego image
- `-o` : Output file for the extracted message (optional)
- `--bits` : Must match the value used when hiding (optional; default: `1`)

## Examples

Hide a text message in a sample cover image:

```bash
python finalproject.py -hide -m secret.txt -c 8-bit/1_08.bmp -o stego.bmp
```

Hide random bits:

```bash
python finalproject.py -hide -m random -c 8-bit/1_08.bmp -o stego.bmp
```

Extract a message:

```bash
python finalproject.py -extract -s stego.bmp -o recovered.txt
```

Hide and extract using 2 bits per pixel:

```bash
python finalproject.py -hide -m secret.txt -c 8-bit/1_08.bmp -o stego.bmp --bits 2
python finalproject.py -extract -s stego.bmp -o recovered.txt --bits 2
```

