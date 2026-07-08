import argparse
from pathlib import Path
from PIL import Image


def parse_arguments():
    """Configures and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A CLI tool to read and display image dimensions."
    )

    # Positional argument for the image path
    parser.add_argument(
        "--hide",
        metavar="FILE_PATH",
        help="Path to the input image file (e.g., path/to/image.jpg)",
    )

    return parser.parse_args()


def process_image(image_path_str: str):
    """Safely opens the image file and extracts basic metadata."""
    path = Path(image_path_str)

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
            palette = img.getpalette(rawmode="BGR")
            if palette is not None:
                print(f"Palette       : {palette}")
                print(f"Palette       : {len(palette)}")
            else: 
                print("Image has no palette")
            
            
           

    except Exception as e:
        print(f"Error reading image: {e}")


def main():
    """Main execution block."""
    args = parse_arguments()
    process_image(args.hide)


if __name__ == "__main__":
    main()
