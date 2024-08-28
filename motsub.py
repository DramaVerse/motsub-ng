import os
import time
import sys
import importlib.util
import subprocess
from datetime import datetime

# 获取当前脚本的绝对路径
current_script_path = os.path.abspath(__file__)

# 获取backend/main.py的绝对路径
backend_main_path = os.path.join(os.path.dirname(
    current_script_path), 'backend', 'main.py')

# 使用importlib.util来导入main模块
spec = importlib.util.spec_from_file_location(
    "backend.main", backend_main_path)
backend_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main)

# 现在我们可以从backend_main模块中获取extract_subtitle函数
extract_subtitle = backend_main.extract_subtitle

# 导入motsub_cord中的get_subtitle_coordinates函数
motsub_cord_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_cord.py')
spec = importlib.util.spec_from_file_location("motsub_cord", motsub_cord_path)
motsub_cord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_cord)
get_subtitle_coordinates = motsub_cord.get_subtitle_coordinates

# 导入motsub_stt中的process_audio_to_srt函数
motsub_stt_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_stt.py')
spec = importlib.util.spec_from_file_location("motsub_stt", motsub_stt_path)
motsub_stt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_stt)
process_audio_to_srt = motsub_stt.process_audio_to_srt


def get_video_path():
    default_path = os.path.expanduser("~/Downloads/1.mp4")
    user_input = input(f"请输入要处理的视频文件路径（直接回车是 {default_path}）：")
    return user_input if user_input else default_path


def extract_audio(video_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"{timestamp}_audio.mp3"
    audio_path = os.path.join(temp_dir, audio_filename)

    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path}"
    subprocess.run(command, shell=True, check=True)
    return audio_path


# Import the new motsub_gpt module
motsub_gpt_path = os.path.join(os.path.dirname(
    current_script_path), 'motsub_gpt.py')
spec = importlib.util.spec_from_file_location("motsub_gpt", motsub_gpt_path)
motsub_gpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motsub_gpt)
compare_and_translate_subtitles = motsub_gpt.compare_and_translate_subtitles


def process_video(video_path, coordinates):
    print(f"你标记的坐标是：{coordinates}")

    print("正在提取音频...")
    audio_path = extract_audio(video_path)
    print(f"音频提取完成：{audio_path}")

    print("正在进行语音识别...")
    try:
        stt_srt_file = process_audio_to_srt(audio_path)
        print(f"语音识别完成，生成字幕文件：{stt_srt_file}")
    except Exception as e:
        print(f"语音识别过程中发生错误: {str(e)}")
        return

    print("正在进行OCR识别...")
    try:
        ocr_srt_file = extract_subtitle(video_path, coordinates)
        print(f"OCR识别完成，生成字幕文件：{ocr_srt_file}")
    except Exception as e:
        print(f"OCR识别过程中发生错误: {str(e)}")
        ocr_srt_file = None

    print("正在比对STT和OCR结果...")
    print("正在生成最终字幕文件...")
    try:
        chinese_srt, arabic_srt = compare_and_translate_subtitles(
            stt_srt_file, ocr_srt_file)
        print(f"比对完成，生成最终中文字幕文件：{chinese_srt}")
        print(f"翻译完成，生成阿拉伯语字幕文件：{arabic_srt}")
    except Exception as e:
        print(f"比对和翻译过程中发生错误: {str(e)}")
        chinese_srt, arabic_srt = None, None

    print("所有处理步骤完成。")
    print(f"STT字幕文件：{stt_srt_file}")
    if ocr_srt_file:
        print(f"OCR字幕文件：{ocr_srt_file}")
    if chinese_srt:
        print(f"最终中文字幕文件：{chinese_srt}")
    if arabic_srt:
        print(f"阿拉伯语字幕文件：{arabic_srt}")

    # 模拟后续处理步骤
    steps = [
        "正在嵌入字幕到视频"
    ]

    for step in steps:
        time.sleep(1)
        print(step + "...完成")

def main():
    video_path = get_video_path()

    print("正在启动图形界面以标注字幕区域...")
    coordinates = get_subtitle_coordinates(video_path)

    if coordinates:
        coordinates = tuple(map(int, coordinates.split()))
        process_video(video_path, coordinates)
    else:
        print("未选择字幕区域，将自动检测。")
        process_video(video_path, None)


if __name__ == "__main__":
    main()
