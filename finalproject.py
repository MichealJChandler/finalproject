import argparse
from pathlib import Path
from PIL import Image
from dataclasses import dataclass
from typing import Tuple
from itertools import batched


@dataclass
class ColorData:
    variance: float
    bgr: Tuple[int, int, int]
    binary: int


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


def process_image(image_path_str: str):
    """Safely opens the image file and extracts basic metadata."""
    path = Path(image_path_str)
    print("path")

    # Validate that the file actually exists
    if not path.is_file():
        print(f"Error: The file '{image_path_str}' does not exist.")
        return

    try:
        # Open and load the image using Pillow
        with Image.open(path) as img:
            print(f"Successfully loaded: {path.name}")
            print(f"Image Format     : {img.format}")
            print(f"Image Size       : {img.width}x{img.height} pixels")
            print(f"Color Mode       : {img.mode}")
            palette = img.getpalette(rawmode="BGR")
            if palette is not None:
                createPalette(palette)
            else: 
                if img.mode == "1":
                    print("Image is a 1-bit pixel image")
                else:
                    print("Image has no palette")
            
            
           

    except Exception as e:
        print(f"Error reading image: {e}")


# Creates the temp palette, with variances and spot for binary
def createPalette(palette: list):

    sorted_palette = [] # initialize the sorted palette 

# loop through each 3 entries of the palette from the 
    for chunk in batched(palette, 3):
        bgr = (chunk[0], chunk[1], chunk[2])
        paletteEntry = ColorData(variance=calcVariance(bgr),bgr=bgr, binary=0)
        sorted_palette.append(paletteEntry)

    sorted_palette.sort(key=lambda item: item.variance)

    for i in sorted_palette:
        i.binary = 1

    print(sorted_palette)
    print(len(sorted_palette))

    # print(sorted_palette)
    

# Calculates the Variance
def calcVariance(bgr: tuple):
    variance = .114 * bgr[0] + .587 * bgr[1] + .299 * bgr[2]
    return round(variance, 3) # Round variance to 3 decimal places

def main():
    """Main execution block."""
    args = parse_arguments()
    if args.hide:
        process_image(args.hide[1])


if __name__ == "__main__":
    main()
