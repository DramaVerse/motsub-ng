import os
import anthropic
from typing import Tuple


def compare_and_translate_subtitles(stt_srt_path: str, ocr_srt_path: str) -> Tuple[str, str]:
    # Read the contents of both SRT files
    with open(stt_srt_path, 'r', encoding='utf-8') as f:
        stt_content = f.read()

    with open(ocr_srt_path, 'r', encoding='utf-8') as f:
        ocr_content = f.read()

    # Initialize the Anthropic client
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    # Prepare the prompt for Claude
    prompt = f"""对比这两个字幕文件（一个来自语音识别，一个来自OCR），生成正确版本的中文字幕，然后生成对应的阿拉伯语字幕。
注意：
1. 这是竖屏视频，宽度和换行可能需要调整。
2. 时间轴必须准确。
3. 格式需要遵循SRT标准。

请返回校对后的中文和阿拉伯语两个单独的SRT文本。

STT字幕内容：
{stt_content}

OCR字幕内容：
{ocr_content}
"""

    # Call the Anthropic API
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        temperature=0.7,
        system="你是一个专业的字幕编辑和翻译专家。",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the Chinese and Arabic subtitles from the response
    response_content = message.content

    # Split the response into Chinese and Arabic parts
    chinese_srt, arabic_srt = response_content.split("阿拉伯语字幕：")

    # Remove any potential system messages or explanations
    chinese_srt = chinese_srt.split("中文字幕：")[-1].strip()
    arabic_srt = arabic_srt.strip()

    # Generate file paths for the new SRT files
    base_dir = os.path.dirname(stt_srt_path)
    chinese_srt_path = os.path.join(base_dir, "final_chinese.srt")
    arabic_srt_path = os.path.join(base_dir, "final_arabic.srt")

    # Write the new SRT files
    with open(chinese_srt_path, 'w', encoding='utf-8') as f:
        f.write(chinese_srt)

    with open(arabic_srt_path, 'w', encoding='utf-8') as f:
        f.write(arabic_srt)

    return chinese_srt_path, arabic_srt_path
