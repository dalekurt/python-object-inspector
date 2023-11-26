# src/inspector.py
"""
inspect.py - Object Inspection Module
"""
import argparse
import base64
import hashlib
import json
import os
import secrets
import string
import time
from io import BytesIO
from json import JSONEncoder

import magic
import mutagen
import piexif
from loguru import logger
from minio import Minio
from minio.error import S3Error
from moviepy.editor import AudioFileClip, VideoFileClip
from mutagen import File

# from mutagen import MutagenError, MutagenFormatError
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

# Minio configurations
# TODO: Use env var
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")

# Ensure the required environment variables are set
if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY):
    raise ValueError(
        "Please set the MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY environment variables."
    )


# Initialize Minio client
def initialize_minio_client(endpoint, access_key, secret_key, secure=False):
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


class Object:
    def __init__(self, file_path):
        """
        Initialize an Object instance with the provided file path.

        Args:
            file_path (str): The path to the file to inspect.
        """
        self.file_path = file_path


class InspectObject(Object):
    def __init__(self, minio_client, object_path):
        super().__init__(object_path)
        self.minio_client = minio_client
        self.object_path = object_path

    def read_object(self):
        """
        Read the content of the file and return it as bytes.

        Returns:
            bytes: The content of the file.
        """
        try:
            bucket_name, object_name = self.object_path.split("/")
            object_data = self.minio_client.get_object(bucket_name, object_name)
            content = object_data.read()
            return content
        except S3Error as e:
            print(f"Error fetching the object from Minio: {e}")
            return None

    def determine_file_type(self):
        """
        Determine the type of the file based on its content.

        Returns:
            str: The file type ('text', 'image', 'video', 'audio', or 'unknown').
        """

        content = self.read_object()
        if content:
            # Initialize the magic library
            mime = magic.Magic()
            mime_type = mime.from_buffer(content)

            # Map MIME types to file types
            mime_type_mapping = {
                "audio": "audio",
                "text": "text",
                "image": "image",
                "video": "video",
            }

            # Check if the MIME type corresponds to a known file type
            for mime_type_keyword, file_type in mime_type_mapping.items():
                if mime_type_keyword in mime_type:
                    return file_type

            # Check for MP3 files specifically
            if "MPEG" in mime_type:
                return "audio"

        return "unknown"

    def is_audio(self, content):
        # TODO: Implement your audio format detection logic here
        # For simplicity, this example checks if the content starts with "RIFF" (common for WAV files)
        return content.startswith(b"RIFF")

    def extract_image_metadata(self):
        """
        Extract metadata from an image object.

        Returns:
            dict: Metadata information for image objects.
        """
        try:
            image_data = self.read_object()
            if image_data is not None:
                image = Image.open(BytesIO(image_data))

                # Extract EXIF metadata using piexif
                exif_data = None
                try:
                    exif_dict = piexif.load(image.info["exif"])
                    exif_data = dict(exif_dict)
                    # Convert binary data to base64-encoded strings
                    for key, value in exif_data.items():
                        if isinstance(value, bytes):
                            exif_data[key] = base64.b64encode(value).decode("utf-8")
                except (KeyError, ValueError, piexif.InvalidImageDataError):
                    exif_data = {}

                # Image metadata fields for photos taken by an iPhone
                image_metadata = {
                    "file_type": "image",
                    "file_format": image.format,
                    "color_mode": image.mode,
                    "image_width": image.width,
                    "image_height": image.height,
                    "exif_data": exif_data,
                }

                return image_metadata
        except Exception as e:
            print(f"Error extracting image metadata: {e}")
            return None

            # Extract GPS data if available
            gps_data = {}
            if "GPSInfo" in exif_data:
                for tag, value in exif_data["GPSInfo"].items():
                    tag_name = GPSTAGS.get(tag, tag)
                    gps_data[tag_name] = value

            # Image metadata fields for photos
            image_metadata = {
                "file_type": "image",
                "file_format": image_format,
                "color_mode": image_mode,
                "image_width": image_width,
                "image_height": image_height,
                "exif_data": exif_data,
                "gps_data": gps_data,
                "camera_make": exif_data.get("Make", ""),
                "camera_model": exif_data.get("Model", ""),
                "exposure_time": exif_data.get("ExposureTime", ""),
                "aperture": exif_data.get("FNumber", ""),
                "iso_speed": exif_data.get("ISOSpeedRatings", ""),
                "focal_length": exif_data.get("FocalLength", ""),
                "date_time": exif_data.get("DateTimeOriginal", ""),
                "title": exif_data.get("ImageDescription", ""),
                "keywords": exif_data.get("Keywords", ""),
                "creator": exif_data.get("Artist", ""),
                "copyright": exif_data.get("Copyright", ""),
            }

            return image_metadata

        except Exception as e:
            print(f"Error extracting image metadata: {e}")
            return None

    def extract_video_metadata(self):
        """
        Extract metadata from a video object.

        Returns:
            dict: Metadata information for video objects.
        """
        try:
            video_data = self.read_object()
            if video_data is not None:
                # Get the size of the video data
                video_size = len(video_data)

                # Create a unique temporary file name with a timestamp and a prefixed random 8-character name
                timestamp = int(time.time())
                random_name = "".join(
                    secrets.choice(string.ascii_lowercase) for _ in range(8)
                )
                prefix = "video"  # Prefix for the random name
                temp_video_file_path = f"/tmp/{prefix}_{random_name}_{timestamp}.mp4"
                with open(temp_video_file_path, "wb") as temp_video_file:
                    temp_video_file.write(video_data)

                # Read video metadata from the temporary file
                video = VideoFileClip(temp_video_file_path)
                duration = video.duration
                frame_rate = video.fps
                resolution = video.size
                audio_info = self.extract_audio_metadata(video.audio)

                # Extract additional video metadata
                video_metadata = {
                    "file_type": "video",
                    "size": video_size,
                    "duration": duration,
                    "frame_rate": frame_rate,
                    "resolution": resolution,
                    "title": getattr(video, "title", ""),  # Title of the video
                    "author": getattr(
                        video, "author", ""
                    ),  # Author/creator of the video
                    "copyright": getattr(
                        video, "copyright", ""
                    ),  # Copyright information
                    "bitrate": getattr(video, "bitrate", 0),  # Bitrate in kbps
                    "container": getattr(
                        video, "container", ""
                    ),  # Video container format
                    "video_codec": getattr(
                        video, "video_codec", ""
                    ),  # Video codec used
                    "video_bitrate": getattr(
                        video, "video_bitrate", 0
                    ),  # Video bitrate in kbps
                    "audio_codec": getattr(
                        video, "audio_codec", ""
                    ),  # Audio codec used
                    "audio_channels": getattr(
                        video, "audio_channels", 0
                    ),  # Number of audio channels
                    "audio_bitrate": getattr(
                        video, "audio_bitrate", 0
                    ),  # Audio bitrate in kbps
                }

                # Remove the temporary file
                os.remove(temp_video_file_path)

                return video_metadata
        except Exception as e:
            print(f"Error extracting video metadata: {e}")
            return None

    def extract_audio_metadata(self, is_video=False):
        """
        Extract audio metadata from a video file.

        Args:
            is_video (bool): Set to True if the file is a video.

        Returns:
            dict: Audio metadata information.
        """
        try:
            audio_data = self.read_object()
            if audio_data is not None:
                # Get the size of the audio data
                audio_size = len(audio_data)

                if is_video:
                    # If it's a video, use moviepy to extract audio metadata
                    video = VideoFileClip(self.file_path)
                    audio = video.audio
                    audio_channels = getattr(audio, "nchannels", 0)
                    audio_bitrate = getattr(audio, "bitrate", 0)
                    audio_codec = "Unknown"
                else:
                    # If it's an audio file, use mutagen to extract audio metadata
                    with BytesIO(audio_data) as temp_audio_file:
                        metadata = File(temp_audio_file)
                        if metadata is not None:
                            audio_channels = metadata.info.channels
                            audio_bitrate = metadata.info.bitrate
                            audio_codec = getattr(
                                metadata.info, "codec_name", "Unknown"
                            )
                        else:
                            return None

                audio_metadata = {
                    "file_type": "audio",
                    "size": audio_size,
                    "audio_codec": audio_codec,
                    "audio_channels": audio_channels,
                    "audio_bitrate": audio_bitrate,
                }

                return audio_metadata
        except Exception as e:
            print(f"Error extracting audio metadata: {e}")
            return None

    def generate_metadata(self):
        """
        Generate metadata for the provided file.

        Returns:
            dict or None: Metadata information for the file.
        """
        data = self.read_object()
        if data:
            file_type = self.determine_file_type()
            filename = os.path.basename(self.file_path)
            content_hash = hashlib.sha256(data).hexdigest()

            metadata = {}  # Create an empty metadata dictionary

            if file_type == "text":
                content = data.decode("utf-8")
                word_count = len(content.split())
                char_count = len(content)
                metadata = {
                    "file_type": file_type,
                    "filename": filename,
                    "word_count": word_count,
                    "char_count": char_count,
                }

            elif file_type == "image":
                image_metadata = self.extract_image_metadata()
                if image_metadata:
                    image_metadata["filename"] = filename
                    image_metadata["content_hash"] = content_hash

                    # Convert the bytes data to a base64-encoded string
                    content_base64 = base64.b64encode(data).decode("utf-8")
                    image_metadata["content_base64"] = content_base64

                    metadata = image_metadata

            elif file_type in ["video", "audio"]:
                is_video = file_type == "video"
                audio_metadata = self.extract_audio_metadata(is_video)
                if audio_metadata:
                    audio_metadata["filename"] = filename
                    audio_metadata["content_hash"] = content_hash

                    # Convert the bytes data to a base64-encoded string
                    content_base64 = base64.b64encode(data).decode("utf-8")
                    audio_metadata["content_base64"] = content_base64

                    metadata = audio_metadata

            else:
                metadata = {
                    "file_type": "unknown",
                    "filename": filename,
                    "content_hash": content_hash,
                }

                # Convert the bytes data to a base64-encoded string
                content_base64 = base64.b64encode(data).decode("utf-8")
                metadata["content_base64"] = content_base64

            return metadata


class CustomJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder to handle special data types.

    This custom JSON encoder extends the JSONEncoder class to handle specific data types when serializing objects to JSON.

    Attributes:
        None

    Methods:
        default(self, obj): Convert special data types to JSON serializable objects.

    Usage:
        Use this class as the JSON encoder when encoding data to JSON to handle custom serialization logic for specific data types.

    Example:
        custom_encoder = CustomJSONEncoder()
        json_data = custom_encoder.encode(data)
    """

    def default(self, obj):
        """
        Convert special data types to JSON serializable objects.

        This method is called during the JSON encoding process and is used to handle specific data types.

        Args:
            obj: The object to be serialized to JSON.

        Returns:
            JSON serializable object.

        Example:
            custom_encoder = CustomJSONEncoder()
            json_data = custom_encoder.encode(data)
        """
        if isinstance(obj, bytes):
            # If it's binary data (bytes), return it as base64-encoded string
            # return obj.hex()
            return base64.b64encode(obj).decode("utf-8")
        return super().default(obj)


def main():
    """
    Entry point of the object inspection application for Minio objects.

    Parses command-line arguments, initializes the Minio client, and inspects the specified Minio object.

    Usage:
    python main.py <object_path>

    Args:
        object_path (str): Full path to the object in the format 'bucket_name/object_name'.

    Returns:
        None
    """
    # Add log file for writing logs to a file
    logger.add("app.log", rotation="5 MB", level="INFO")

    parser = argparse.ArgumentParser(description="File Inspector for Minio Objects")
    parser.add_argument(
        "object_path",
        help="Full path to the object in the format 'bucket_name/object_name'",
    )
    args = parser.parse_args()

    try:
        # Initialize Minio client
        minio_client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,  # Set to True if using HTTPS
        )

        # Create an InspectObject instance
        inspector = InspectObject(minio_client, args.object_path)

        # Inspect the object
        content = inspector.read_object()

        if content:
            logger.info("Inspecting object '{args.object_path}':")
            metadata = inspector.generate_metadata()

            if metadata:
                # Use the CustomJSONEncoder to serialize the metadata
                custom_encoder = CustomJSONEncoder(indent=4)
                metadata_json = custom_encoder.encode(metadata)
                logger.info("Metadata:")
                logger.info(metadata_json)
            else:
                logger.warning(
                    f"Failed to generate metadata for object '{args.object_path}'"
                )
        else:
            logger.warning(f"Failed to read content from object '{args.object_path}'")

    except S3Error as e:
        logger.error(f"Minio S3 Error: {e}")
    except Exception as e:
        # Log any exceptions that occur
        logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
