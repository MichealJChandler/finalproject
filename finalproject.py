import argparse
from pathlib import Path
from PIL import Image
from dataclasses import dataclass
from typing import Tuple
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

    # Flag detection --hide .\Host Image .\Message Data
    parser.add_argument(
        "--hide",
        nargs='+',
        help="Path to the input image file (e.g., path/to/image.jpg)",
    )

    return parser.parse_args()


def process_image(message_image_path: str, host_image_path: str):

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
            print(f"Successfully loaded: {host_path.name}")
            print(f"Image Format     : {host_img.format}")
            print(f"Image Size       : {host_img.width}x{host_img.height} pixels")
            print(f"Color Mode       : {host_img.mode}")
            host_palette = host_img.getpalette(rawmode="BGR")
            if host_palette is not None:
                sorted_palette, palette_lookup = createPalette(host_palette)
                host_image = host_img.get_flattened_data()  # Load host image pixels
                try:
                    with Image.open(message_path) as message_img:
                        print(f"Successfully loaded: {message_path.name}")
                        print(f"Image Format     : {message_img.format}")
                        print(f"Image Size       : {message_img.width}x{message_img.height} pixels")
                        print(f"Color Mode       : {message_img.mode}")
                        message_palette = message_img.getpalette(rawmode="BGR")
                        if message_palette is not None:
                            message_image = message_img.get_flattened_data()  # Load message image pixels
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
def createPalette(palette: list):

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

    print("Sorted Palette:")
    print(sorted_palette)

    for position, entry in enumerate(sorted_palette):
        palette_lookup[entry.original] = position


    return sorted_palette, palette_lookup

    

# Calculates the luminance
def calcLuminance(bgr: tuple):
    luminance = .114 * bgr[0] + .587 * bgr[1] + .299 * bgr[2]
    return round(luminance, 3) # Round luminance to 3 decimal places

def deteremineBit(pixel_index, palette_lookup):
    position = palette_lookup[pixel_index]
    return position % 2

def getPartner(pixel_index, sorted_palette, palette_lookup):
    position = palette_lookup[pixel_index]
    if position % 2 == 0:
        return sorted_palette[position + 1].original
    else:
        return sorted_palette[position - 1].original

def main():
    """Main execution block."""
    args = parse_arguments()
    if args.hide:
        process_image(args.hide[0], args.hide[1])


if __name__ == "__main__":
    main()
