import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping

from mcap.writer import Writer


def has_message(dir_path: Path):
    """iterate all files in the directory and check if there is png file"""
    for file in dir_path.iterdir():
        if file.is_file() and file.suffix == ".png":
            return True
    return False


def register_channels(writer: Writer, schema_id: int, dir_path: Path) -> Mapping[str, int]:
    """
    register channels for all subdirectories with png files,
    topic is the relative path to the dir_path.
    Note that we iterate all subdirectories, not just the direct children.

    Returns:
        A mapping from relative path to channel_id
    """
    channel_id_map = {}
    for sub_dir in dir_path.rglob("*"):
        if sub_dir.is_dir() and has_message(sub_dir):
            topic = str(sub_dir.relative_to(dir_path))
            channel_id = writer.register_channel(
                schema_id=schema_id,
                topic=topic,
                message_encoding="json",
            )
            channel_id_map[topic] = channel_id
    return channel_id_map


def get_ts_from_file_path(file_path: Path) -> int:
    """get timestamp from file name"""
    return int(file_path.stem)


def convert_data_to_mcap(input_dir: Path, output_file: Path):
    with output_file.open("wb") as out_stream:
        writer = Writer(out_stream)
        writer.start()

        schema_id = writer.register_schema(
            name="foxglove.CompressedImage",
            encoding="jsonschema",
            data=json.dumps(
                {
                    "title": "foxglove.CompressedImage",
                    "description": "A compressed image",
                    "type": "object",
                    "properties": {
                        "timestamp": {
                            "type": "object",
                            "title": "time",
                            "properties": {
                                "sec": {
                                    "type": "integer",
                                    "minimum": 0
                                },
                                "nsec": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 999999999
                                }
                            },
                            "description": "Timestamp of image"
                        },
                        "frame_id": {
                            "type": "string",
                            "description": "Frame of reference for the image. The origin of the frame is the optical center of the camera. +x points to the right in the image, +y points down, and +z points into the plane of the image."
                        },
                        "data": {
                            "type": "string",
                            "contentEncoding": "base64",
                            "description": "Compressed image data"
                        },
                        "format": {
                            "type": "string",
                            "description": "Image format\n\nSupported values: image media types supported by Chrome, such as `webp`, `jpeg`, `png`"
                        }
                    }
                }
            ).encode(),
        )

        channel_id_map = register_channels(writer, schema_id, input_dir)

        for file_path in sorted(input_dir.rglob("*.png")):
            with file_path.open("rb") as png_data:
                raw_data = png_data.read()
            topic = str(file_path.parent.relative_to(input_dir))
            channel_id = channel_id_map[topic]

            cur_time = get_ts_from_file_path(file_path)
            data = {
                "timestamp": {
                    "sec": cur_time // 1_000,
                    "nsec": (cur_time % 1_000) * 1_000_000,
                },
                "frame_id": "camera",
                "data": base64.b64encode(raw_data).decode("utf-8"),
                "format": "jpeg",
            }
            writer.add_message(
                channel_id=channel_id,
                log_time=cur_time * 1_000_000,
                data=json.dumps(data).encode(),
                publish_time=cur_time * 1_000_000,
            )


def main():
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    sample_dirs = [d for d in input_dir.rglob("*") if d.is_dir() and d.name.startswith("sample")]

    for sample_dir in sample_dirs:
        sample_relative_path = sample_dir.relative_to(input_dir)
        output_file = output_dir / f"{sample_relative_path}.mcap"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        convert_data_to_mcap(sample_dir, output_file)

        # recover mcap file
        output_recover_file = output_dir / f"{sample_relative_path}.recover.mcap"
        time.sleep(0.5)
        subprocess.run(f"mcap recover {output_file} -o {output_recover_file}", shell=True)

        # delete original mcap file for space saving
        output_file.unlink()


if __name__ == "__main__":
    main()
