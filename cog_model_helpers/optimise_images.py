import os
import shutil
from typing import List
from concurrent.futures import ThreadPoolExecutor

from cog import Input, Path
from PIL import Image

IMAGE_FILE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
FORMAT_CHOICES = ["webp", "jpg", "png"]
DEFAULT_FORMAT = "webp"
DEFAULT_QUALITY = 95

executor = ThreadPoolExecutor(max_workers=10)


def predict_output_format() -> str:
    return Input(
        description="Format of the output images",
        choices=FORMAT_CHOICES,
        default=DEFAULT_FORMAT,
    )


def predict_output_quality() -> int:
    return Input(
        description="Quality of the output images, from 0 to 100. 100 is best quality, 0 is lowest quality.",
        default=DEFAULT_QUALITY,
        ge=0,
        le=100,
    )


def should_optimise_images(output_format: str, output_quality: int):
    return output_quality < 100 or output_format in [
        "webp",
        "jpg",
    ]


def move_file(src, dst):
    return shutil.move(src, dst)


def optimise_image_files(
    output_format: str = DEFAULT_FORMAT, output_quality: int = DEFAULT_QUALITY, files: List[Path] = [], return_url: bool = False, s3_path: str = ""
) -> List[Path]:
    if should_optimise_images(output_format, output_quality):
        optimised_files = []
        for file in files:
            if file.is_file() and file.suffix in IMAGE_FILE_EXTENSIONS:
                image = Image.open(file)
                optimised_file_path = file.with_suffix(f".{output_format}")
                image.save(
                    optimised_file_path,
                    quality=output_quality,
                    optimize=True,
                )
                optimised_files.append(optimised_file_path)
            else:
                optimised_files.append(file)

        to_return = optimised_files
    else:
        to_return = files
    if return_url:
        for file in to_return:
            shutil.move(file.as_posix(), os.path.join(s3_path, file.name))
        return []
    else:
        for file in to_return:
            _ = executor.submit(move_file, file.as_posix(), os.path.join(s3_path, file.name))
        return to_return
