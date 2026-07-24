import argparse
from pathlib import Path
from PIL import Image
from dataclasses import dataclass
from typing import Tuple
from itertools import batched
from typing import Optional


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

    # Flag detection --hide .\Host Image .\Message Data
    parser.add_argument(
        "--hide",
        nargs='+',
        help="Path to the input image file (e.g., path/to/image.jpg)",
    )

    parser.add_argument(
        "--bits",
        type=int,
        choices=range(1,9),
        default=1,
        help="Number of bits to hide per pixel (1-8). Default is 1.",
    )

    return parser.parse_args()


def process_image(message_image_path: str, host_image_path: str, num_bits: int):

    """Safely opens the image file and extracts basic metadata."""
    message_path = Path(message_image_path)
    host_path = Path(host_image_path)

    # Validate that the file actually exists
    if not message_path.is_file():
        print(f"Error: The file '{message_image_path}' does not exist.")
        return
    if not host_path.is_file():
        print(f"Error: The file '{host_image_path}' does not exist.")
        return

    try:
        # Open and load the image using Pillow
        with Image.open(host_path) as host_img:
            host_palette = host_img.getpalette(rawmode="BGR")
            if host_palette is not None:
                sorted_palette, palette_lookup = createPalette(host_palette)
                host_image = host_img.get_flattened_data()  # Load host image pixels
                try:
                    with Image.open(message_path) as message_img:
                        message_palette = message_img.getpalette(rawmode="BGR")
                        if message_palette is not None:
                            message_image = message_img.get_flattened_data()  # Load message image pixels
                            message_values = convertMessagetoValues(message_image, num_bits)
                            message_values = addMessageLength(message_values, num_bits)
                            embedded_image, embedded_count = embedMessageIntoHost(host_image, message_values, sorted_palette, palette_lookup, num_bits)
                            if embedded_count < len(message_values):
                                print("Warning: Message was too large.")
                                print(f"Embedded {embedded_count}/{len(message_values)} values.")
                            else:
                                print("Message fully embedded.")

                            host_img.putdata(embedded_image)
                            host_img.save("hidden_image.bmp")
                except Exception as e:
                    print(f"Error reading image: {e}")
            else: 
                if host_img.mode == "1":
                    print("Image is a 1-bit pixel image")
                else:
                    print("Image has no palette")
    except Exception as e:
        print(f"Error reading image: {e}")


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

def convertMessagetoValues(message_image, num_bits: int):
    """Converts the message image to a list of bits."""
    message_values = []
    for pixel in message_image:
        bits = format(pixel, '08b')  # Convert pixel value to 8-bit binary
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
    """Main execution block."""
    args = parse_arguments()
    if args.hide:
        process_image(args.hide[0], args.hide[1], args.bits)


if __name__ == "__main__":
    main()
