import shutil
import argparse
from pathlib import Path
import sys
from typing import List, Set


def get_image_files(input_dir: Path, extensions: Set[str]) -> List[Path]:
    """Get image files (only in first-level subdirectories) with matching extensions."""
    return [
        file
        for folder in input_dir.iterdir() if folder.is_dir()
        for file in folder.iterdir() if file.suffix.lower() in extensions
    ]


def get_unique_base(output_dir: Path, base: str, ext: str) -> str:
    """Find a unique base name efficiently without excessive looping."""
    candidate = base
    counter = 1
    existing_files = {f.stem for f in output_dir.glob("*")}  # Cache existing filenames for faster lookup

    while candidate in existing_files:
        candidate = f"{base}_{counter}"
        counter += 1

    return candidate


def generate_gt_from_folders(input_dir: Path, output_dir: Path) -> int:
    """Generate .gt.txt files for each image where the text file contains the parent folder's name."""
    print("Ground-Truth generation beginning...")
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'}
    image_files = get_image_files(input_dir, image_extensions)

    total_files = 0

    for file_path in image_files:
        folder_name = file_path.parent.name
        base_name = file_path.stem
        ext = file_path.suffix.lower()

        unique_base = get_unique_base(output_dir, base_name, ext)
        dest_image = output_dir / f"{unique_base}{ext}"
        txt_filepath = output_dir / f"{unique_base}.gt.txt"

        try:
            txt_filepath.write_text(folder_name, encoding='utf-8')
            shutil.copy(file_path, dest_image)  # Faster than copy2()
            total_files += 1
            print(f"Processed: {file_path.name} -> {folder_name}")
        except (IOError, OSError) as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    print(f"Done! Processed {total_files} image files.")
    return total_files


def main():
    parser = argparse.ArgumentParser(description="Generate .gt.txt files from folder names for Tesseract training")
    parser.add_argument('input_dir', type=Path, help='Input directory containing subfolders with images')
    parser.add_argument('output_dir', type=Path, help='Output directory')
    args = parser.parse_args()

    count = generate_gt_from_folders(args.input_dir.resolve(), args.output_dir.resolve())
    if count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()