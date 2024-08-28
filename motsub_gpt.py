import anthropic
import logging
import json
import os
from typing import Tuple, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hardcoded API key (not recommended for production use)
ANTHROPIC_API_KEY = "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"

def test_api_key():
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hello, Claude!"}]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        logger.info("API key is valid")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"API key test failed: {str(e)}")
        return False

def text_block_to_dict(obj):
    if isinstance(obj, anthropic.types.TextBlock):
        return {'type': 'text', 'text': obj.text}
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def save_claude_response(response_content, base_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"claude_response_{timestamp}.json"
    filepath = os.path.join(base_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(response_content, f, ensure_ascii=False, indent=2, default=text_block_to_dict)
    
    logger.info(f"Claude's response saved to: {filepath}")
    return filepath

def compare_and_translate_subtitles(stt_srt_path: str, ocr_srt_path: str) -> Tuple[Optional[str], Optional[str]]:
    logger.info("Starting subtitle comparison and translation process")

    if not test_api_key():
        logger.error("API key is invalid. Please check your API key and try again.")
        return None, None

    try:
        # Read the contents of both SRT files
        logger.info(f"Reading STT subtitle file: {stt_srt_path}")
        with open(stt_srt_path, 'r', encoding='utf-8') as f:
            stt_content = f.read()
        
        logger.info(f"Reading OCR subtitle file: {ocr_srt_path}")
        with open(ocr_srt_path, 'r', encoding='utf-8') as f:
            ocr_content = f.read()

        # Initialize the Anthropic client
        logger.info("Initializing Anthropic client")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Prepare the prompt for Claude
        logger.info("Preparing prompt for Claude")
        prompt = f"""对比这两个字幕文件（一个来自语音识别，一个来自OCR），生成正确版本的中文字幕，然后生成对应的阿拉伯语字幕。
注意：
1. 这是竖屏视频，宽度和换行可能需要调整。
2. 时间轴必须准确。
3. 格式需要遵循SRT标准。

请返回校对后的中文和阿拉伯语两个单独的SRT文本。在返回内容中，请使用"中文字幕："和"阿拉伯语字幕："作为分隔符。

STT字幕内容：
{stt_content}

OCR字幕内容：
{ocr_content}
"""

        # Call the Anthropic API
        logger.info("Calling Anthropic API")
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=8192,
                temperature=0.7,
                system="你是一个专业的字幕编辑和翻译专家。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return None, None

        # Save Claude's complete response
        base_dir = os.path.dirname(stt_srt_path)
        response_file = save_claude_response(message.content, base_dir)
        logger.info(f"Claude's complete response saved to: {response_file}")
        
        # Print Claude's response to console
        print("Claude's response:")
        print(json.dumps(message.content, ensure_ascii=False, indent=2, default=text_block_to_dict))

        # Extract the Chinese and Arabic subtitles from the response
        logger.info("Processing API response")
        response_content = message.content[0].text if isinstance(message.content, list) else message.content
        
        # Split the response into Chinese and Arabic parts
        parts = response_content.split("阿拉伯语字幕：")
        if len(parts) != 2:
            raise ValueError("Unexpected response format from Claude")
        
        chinese_srt = parts[0].split("中文字幕：")[-1].strip()
        arabic_srt = parts[1].strip()

        # Generate file paths for the new SRT files
        chinese_srt_path = os.path.join(base_dir, "final_chinese.srt")
        arabic_srt_path = os.path.join(base_dir, "final_arabic.srt")

        # Write the new SRT files
        logger.info(f"Writing final Chinese subtitle file: {chinese_srt_path}")
        with open(chinese_srt_path, 'w', encoding='utf-8') as f:
            f.write(chinese_srt)
        
        logger.info(f"Writing final Arabic subtitle file: {arabic_srt_path}")
        with open(arabic_srt_path, 'w', encoding='utf-8') as f:
            f.write(arabic_srt)

        logger.info("Subtitle comparison and translation process completed successfully")
        return chinese_srt_path, arabic_srt_path

    except Exception as e:
        logger.error(f"Error in subtitle comparison and translation process: {str(e)}", exc_info=True)
        return None, None

if __name__ == "__main__":
    # This block is for testing purposes
    stt_srt_path = "path/to/your/stt_subtitle.srt"
    ocr_srt_path = "path/to/your/ocr_subtitle.srt"
    chinese_srt, arabic_srt = compare_and_translate_subtitles(stt_srt_path, ocr_srt_path)
    if chinese_srt and arabic_srt:
        print(f"Chinese subtitles saved to: {chinese_srt}")
        print(f"Arabic subtitles saved to: {arabic_srt}")
    else:
        print("Failed to generate subtitles")