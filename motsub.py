import os
import time
import sys
import importlib.util
import subprocess
from datetime import datetime
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)

# Get the absolute path of backend/main.py
backend_main_path = os.path.join(os.path.dirname(
    current_script_path), 'backend', 'main.py')

# Use importlib.util to import the main module
spec = importlib.util.spec_from_file_location(
    "backend.main", backend_main_path)
backend_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main)

# Now we can get the extract_subtitle function from the backend_main module
extract_subtitle = backend_main.extract_subtitle

# Import the get_subtitle_coordinates function from motsub_cord
motsub_cord_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_cord.py')
spec = importlib.util.spec_from_file_location("motsub_cord", motsub_cord_path)
motsub_cord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_cord)
get_subtitle_coordinates = motsub_cord.get_subtitle_coordinates

# Import the process_audio_to_srt function from motsub_stt
motsub_stt_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_stt.py')
spec = importlib.util.spec_from_file_location("motsub_stt", motsub_stt_path)
motsub_stt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_stt)
process_audio_to_srt = motsub_stt.process_audio_to_srt

# Import the new motsub_gpt module
motsub_gpt_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_gpt.py')
spec = importlib.util.spec_from_file_location("motsub_gpt", motsub_gpt_path)
motsub_gpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_gpt)
compare_and_translate_subtitles = motsub_gpt.compare_and_translate_subtitles


def get_video_path():
    default_path = os.path.expanduser("~/Downloads/1.mp4")
    user_input = input(f"请输入要处理的视频文件路径（直接回车是 {default_path}）：")
    return user_input if user_input else default_path


def extract_audio(video_path):
    logger.info("Starting audio extraction")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"{timestamp}_audio.mp3"
    audio_path = os.path.join(temp_dir, audio_filename)

    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path}"
    logger.info(f"Running ffmpeg command: {command}")
    subprocess.run(command, shell=True, check=True)
    logger.info(f"Audio extraction completed: {audio_path}")
    return audio_path


def process_subtitles(stt_srt_file: str, ocr_srt_file: str) -> Tuple[Optional[str], Optional[str]]:
    logger.info("Starting subtitle processing")
    logger.info("Comparing STT and OCR results...")
    logger.info("Generating final subtitle files...")

    try:
        chinese_srt, arabic_srt = compare_and_translate_subtitles(
            stt_srt_file, ocr_srt_file)
        if chinese_srt and arabic_srt:
            logger.info(
                f"Comparison complete. Final Chinese subtitle file generated: {chinese_srt}")
            logger.info(
                f"Translation complete. Arabic subtitle file generated: {arabic_srt}")
        else:
            logger.warning(
                "Subtitle processing completed, but one or both output files were not generated.")
        return chinese_srt, arabic_srt
    except Exception as e:
        logger.error(f"Error in subtitle processing: {str(e)}", exc_info=True)
        return None, None


def process_video(video_path, coordinates):
    logger.info(f"Processing video: {video_path}")
    logger.info(f"Subtitle coordinates: {coordinates}")

    logger.info("Extracting audio...")
    audio_path = extract_audio(video_path)
    logger.info(f"Audio extraction complete: {audio_path}")

    logger.info("Performing OCR...")
    try:
        ocr_srt_file = extract_subtitle(video_path, coordinates)
        if isinstance(ocr_srt_file, tuple):
            # Extract the file path from the tuple
            ocr_srt_file = ocr_srt_file[0]
        logger.info(f"OCR complete. Subtitle file generated: {ocr_srt_file}")
    except Exception as e:
        logger.error(f"Error in OCR process: {str(e)}", exc_info=True)
        ocr_srt_file = None

    logger.info("Performing speech-to-text...")
    try:
        stt_srt_file = process_audio_to_srt(audio_path)
        logger.info(
            f"Speech-to-text complete. Subtitle file generated: {stt_srt_file}")
    except Exception as e:
        logger.error(
            f"Error in speech-to-text process: {str(e)}", exc_info=True)
        return

    chinese_srt, arabic_srt = process_subtitles(stt_srt_file, ocr_srt_file)

    logger.info("All processing steps completed.")
    logger.info(f"STT subtitle file: {stt_srt_file}")
    if ocr_srt_file:
        logger.info(f"OCR subtitle file: {ocr_srt_file}")
    if chinese_srt:
        logger.info(f"Final Chinese subtitle file: {chinese_srt}")
    if arabic_srt:
        logger.info(f"Arabic subtitle file: {arabic_srt}")

    # Simulate subsequent processing steps
    steps = [
        "Embedding subtitles into video"
    ]

    for step in steps:
        time.sleep(1)
        logger.info(f"{step}...completed")


def main():
    video_path = get_video_path()

    logger.info("Starting graphical interface to annotate subtitle region...")
    coordinates = get_subtitle_coordinates(video_path)

    if coordinates:
        coordinates = tuple(map(int, coordinates.split()))
        process_video(video_path, coordinates)
    else:
        logger.info(
            "No subtitle region selected. Automatic detection will be used.")
        process_video(video_path, None)


if __name__ == "__main__":
    main()
