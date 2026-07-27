"""
CS 4463 - Steganography - Team 11
Nearest Luminance Palette Hiding Technique

Kiahna Isadore, Micheal Chandler, William Penrose

A command-line tool to hide a message inside, and extract a message from,
an 8-bit paletted BMP image, using a nearest-luminance-palette substitution
technique instead of plain LSB substitution.
"""

import argparse
import os
from pathlib import Path
from PIL import Image
from dataclasses import dataclass
from typing import Tuple, Optional
from itertools import batched


@dataclass
class ColorData:
    luminance: float
    bgr: Tuple[int, int, int]
    original: int


def parse_arguments():
    # Configures and parses command-line arguments.
    parser = argparse.ArgumentParser(
        description="A CLI tool to read and display image dimensions."
    )
    parser.add_argument(
        "-hide", 
        action="store_true", 
        help="Hide a message in a cover image"
    )
    parser.add_argument(
        "-extract", 
        action="store_true", 
        help="Extract a message from a stego image"
    )
    parser.add_argument(
        "-m", 
        type=str, 
        help="Path to message file, or 'random' for random bits"
    )
    parser.add_argument(
        "-c", 
        type=str, 
        help="Path to cover image file"
    )
    parser.add_argument(
        "-s", 
        type=str, 
        help="Path to stego image file"
    )
    parser.add_argument(
        "-o", 
        type=str, 
        help="Path to output file"
    )
    parser.add_argument(
        "--bits",
        type=int,
        choices=range(1,9),
        default=1,
        help="Number of bits to hide per pixel (1-8). Default is 1.",
    )

    return parser.parse_args()

def get_message_bytes(message_arg: str) -> bytes:
    # generate random data
    if message_arg.lower() == "random":
        print("Generating 256 bytes of random message data...")
        return os.urandom(256) 
    
    msg_path = Path(message_arg)
    if not msg_path.is_file():
        raise FileNotFoundError(f"Error: The message file '{message_arg}' does not exist.")
    
    with open(msg_path, "rb") as f:
        return f.read()

def process_hide(args):
    if not args.m or not args.c:
        print("Error: -hide requires -m <message file> and -c <coverfile>")
        return

    cover_path = Path(args.c)
    if not cover_path.is_file():
        print(f"Error: The cover file '{args.c}' does not exist.")
        return

    output_path = args.o if args.o else "hidden_image.bmp"

    try:
        message_bytes = get_message_bytes(args.m)
        message_values = convertMessagetoValues(message_bytes, args.bits)
        message_values = addMessageLength(message_values, args.bits)

        with Image.open(cover_path) as host_img:
            host_palette = host_img.getpalette(rawmode="BGR")
            if host_palette is None:
                print("Error: Image has no palette.")
                return

            sorted_palette, palette_lookup = createPalette(host_palette)
            host_image = list(host_img.get_flattened_data()) 

            embedded_image, embedded_count = embedMessageIntoHost(
                host_image, message_values, sorted_palette, palette_lookup, args.bits
            )

            if embedded_count < len(message_values):
                print(f"Warning: Message was too large. Embedded {embedded_count}/{len(message_values)} values.")
            else:
                print("Message fully embedded.")

            host_img.putdata(embedded_image)
            host_img.save(output_path)
            print(f"Stego image successfully saved to {output_path}")

    except Exception as e:
        print(f"Error during hiding process: {e}")

def process_extract(args):
    if not args.s:
        print("Error: -extract requires -s <stego file>")
        return

    stego_path = Path(args.s)
    if not stego_path.is_file():
        print(f"Error: The stego file '{args.s}' does not exist.")
        return

    output_path = args.o if args.o else "extracted_message.bin"

    try:
        with Image.open(stego_path) as stego_img:
            if stego_img.getpalette() is None:
                print("Error: Stego image has no palette.")
                return

            stego_data = list(stego_img.get_flattened_data())

            # we read the first 32 bits to retrieve the exact length of the hidden message
            # tells the loop when to stop
            length_bits = 32
            length_chunks_count = len(list(range(0, length_bits, args.bits)))
            
            length_binary = ""
            for i in range(length_chunks_count):
                chunk_val = determineBits(stego_data[i], args.bits)
                actual_chunk_len = min(args.bits, length_bits - i * args.bits)
                length_binary += format(chunk_val, f'0{actual_chunk_len}b')
                
            message_length = int(length_binary, 2)
            
            message_values = []
            start_idx = length_chunks_count
            end_idx = start_idx + message_length
            
            for i in range(start_idx, end_idx):
                if i >= len(stego_data):
                    break 
                chunk_val = determineBits(stego_data[i], args.bits)
                message_values.append(chunk_val)

            message_binary = ""
            for chunk_val in message_values:
                message_binary += format(chunk_val, f'0{args.bits}b')
                
            extracted_bytes = bytearray()
            for i in range(0, len(message_binary), 8):
                byte_chunk = message_binary[i:i+8]
                if len(byte_chunk) == 8: 
                    extracted_bytes.append(int(byte_chunk, 2))

            with open(output_path, "wb") as f:
                f.write(extracted_bytes)
            print(f"Message successfully extracted and saved to {output_path}")

    except Exception as e:
        print(f"Error during extraction process: {e}")


# Creates the sorted palette and the lookup dictionary
def createPalette(palette: list[int]):

    counter = 0
    sorted_palette = [] # initialize the sorted palette 
    palette_lookup = {} # initialize the palette dictionary

# loop through each 3 entries of the palette from the 
    for chunk in batched(palette, 3):
        bgr = (chunk[0], chunk[1], chunk[2])
        paletteEntry = ColorData(luminance=calcLuminance(bgr),bgr=bgr, original=counter)
        sorted_palette.append(paletteEntry)
        counter += 1

    sorted_palette.sort(key=lambda item: item.luminance)

    for position, entry in enumerate(sorted_palette):
        palette_lookup[entry.original] = position


    return sorted_palette, palette_lookup

# Calculates the luminance
def calcLuminance(bgr: tuple):
    luminance = .114 * bgr[0] + .587 * bgr[1] + .299 * bgr[2]
    return round(luminance, 3) # Round luminance to 3 decimal places

def determineBits(pixel_index, num_bits):
    mask = (1 << num_bits) - 1
    return pixel_index & mask

def findNearestMatchingColor(pixel_index, desired_value, sorted_palette, palette_lookup, num_bits):

    position = palette_lookup[pixel_index]
    upper: Optional[ColorData] = None
    lower: Optional[ColorData] = None

    mask = (1 << num_bits) - 1

    # Search upward
    i = position + 1
    while i < len(sorted_palette):
        if (sorted_palette[i].original & mask) == desired_value:
            upper = sorted_palette[i]
            break
        i += 1

    # Search downward
    i = position - 1
    while i >= 0:
        if (sorted_palette[i].original & mask) == desired_value:
            lower = sorted_palette[i]
            break
        i -= 1

    if upper is None:
        if lower is None:
            return None  # No matching color found
        return lower.original
    
    if lower is None:
        return upper.original

    current = sorted_palette[position]

    distance_upper = colorDistance(current.bgr, upper.bgr)
    distance_lower = colorDistance(current.bgr, lower.bgr)
    

    if distance_upper <= distance_lower:
        return upper.original
    else:
        return lower.original

def colorDistance(color1: Tuple[int,int,int],
                  color2: Tuple[int,int,int]) -> int:
    return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2])

def convertMessagetoValues(message_bytes: bytes, num_bits: int):
    message_values = []
    for byte in message_bytes:
        bits = format(byte, '08b')  
        for i in range(0, 8, num_bits):
            chunk = bits[i:i+num_bits]
            if len(chunk) < num_bits:
                chunk = chunk.ljust(num_bits, "0")
            message_values.append(int(chunk, 2))
    return message_values

def embedMessageIntoHost(host_image, message_values, sorted_palette, palette_lookup, num_bits):
    """Embeds the message values into the host image."""

    embedded_image = []
    embedded_count = 0

    for i, pixel in enumerate(host_image):

        # No more message values
        if i >= len(message_values):
            embedded_image.append(pixel)
            continue

        desired_value = message_values[i]
        current_value = determineBits(pixel, num_bits)

        if current_value == desired_value:
            embedded_image.append(pixel)
            embedded_count += 1
        else:
            new_pixel = findNearestMatchingColor(pixel, desired_value, sorted_palette, palette_lookup, num_bits)

            if new_pixel is not None:
                embedded_image.append(new_pixel)
                embedded_count += 1
            else:
                embedded_image.append(pixel)

    return embedded_image, embedded_count

def addMessageLength(message_values, num_bits, length_bits=32):

    message_length = len(message_values)

    length_binary = format(
        message_length,
        f"0{length_bits}b"
    )
    length_values = []
    # Split length into chunks of num_bits
    for i in range(0, length_bits, num_bits):
        chunk = length_binary[i:i+num_bits]
        length_values.append(
            int(chunk, 2)
        )

    return length_values + message_values

def main():
    args = parse_arguments()

    if args.hide:
        process_hide(args)
    elif args.extract:
        process_extract(args)
    else:
        print("Please specify either -hide or -extract. Use -h for help.")

if __name__ == "__main__":
    main()
