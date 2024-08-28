import os
import time
import json
import base64
import hashlib
import hmac
import requests
from datetime import datetime

APPID = "a2e065fe"
SECRET_KEY = "a76ba25b775f082acfe9c1849501a2eb"
SLICE_SIZE = 10485760  # 10MB


class SliceIdGenerator:
    def __init__(self):
        self.__ch = 'aaaaaaaaa`'

    def get_next_slice_id(self):
        ch = self.__ch
        j = len(ch) - 1
        while j >= 0:
            cj = ch[j]
            if cj != 'z':
                ch = ch[:j] + chr(ord(cj) + 1) + ch[j + 1:]
                break
            else:
                ch = ch[:j] + 'a' + ch[j + 1:]
                j = j - 1
        self.__ch = ch
        return self.__ch


def gene_params(apiname, appid, secret_key, file_path=None, task_id=None, slice_id=None):
    ts = str(int(time.time()))
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    signa = str(signa, 'utf-8')

    param_dict = {}
    param_dict['app_id'] = appid
    param_dict['signa'] = signa
    param_dict['ts'] = ts

    if apiname == 'prepare':
        file_len = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        param_dict['file_len'] = str(file_len)
        param_dict['file_name'] = file_name
        param_dict['slice_num'] = str(
            int(file_len / SLICE_SIZE) + (1 if file_len % SLICE_SIZE else 0))
    elif apiname == 'upload':
        param_dict['task_id'] = task_id
        param_dict['slice_id'] = slice_id
    elif apiname in ['merge', 'getProgress', 'getResult']:
        param_dict['task_id'] = task_id

    return param_dict


def send_request(url, data, files=None):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"} if not files else {}
    response = requests.post(url, data=data, files=files, headers=headers)
    result = response.json()

    if result.get("ok") == 0:
        print(f"请求成功: {result}")
        return result
    else:
        print(f"请求失败: {result}")
        raise Exception(f"API request failed: {result.get('failed')}")


def stt_process(audio_file):
    print("开始语音识别过程...")

    # 预处理
    url = "http://raasr.xfyun.cn/api/prepare"
    data = gene_params('prepare', APPID, SECRET_KEY, file_path=audio_file)
    result = send_request(url, data)
    task_id = result["data"]
    print(f"获得任务ID: {task_id}")

    # 上传音频
    url = "http://raasr.xfyun.cn/api/upload"
    sig = SliceIdGenerator()

    with open(audio_file, 'rb') as file_object:
        index = 1
        while True:
            content = file_object.read(SLICE_SIZE)
            if not content:
                break
            slice_id = sig.get_next_slice_id()
            data = gene_params('upload', APPID, SECRET_KEY,
                               task_id=task_id, slice_id=slice_id)
            files = {
                "filename": slice_id,
                "content": content
            }
            send_request(url, data, files)
            print(f'上传分片 {index} 成功')
            index += 1

    # 合并请求
    print("文件上传成功，开始合并请求...")
    url = "http://raasr.xfyun.cn/api/merge"
    data = gene_params('merge', APPID, SECRET_KEY, task_id=task_id)
    send_request(url, data)

    # 获取进度
    url = "http://raasr.xfyun.cn/api/getProgress"
    while True:
        data = gene_params('getProgress', APPID, SECRET_KEY, task_id=task_id)
        result = send_request(url, data)
        progress = json.loads(result["data"])
        if progress["status"] == 9:
            print("任务处理完成")
            break
        print(f"任务进度: {progress['status']}")
        time.sleep(5)

    # 获取结果
    print("开始获取识别结果...")
    url = "http://raasr.xfyun.cn/api/getResult"
    data = gene_params('getResult', APPID, SECRET_KEY, task_id=task_id)
    result = send_request(url, data)

    return json.loads(result["data"])


def generate_srt(stt_result, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, item in enumerate(stt_result, 1):
            start_time = format_time(int(item['bg']))
            end_time = format_time(int(item['ed']))
            text = item['onebest']
            f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")


def format_time(ms):
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def process_audio_to_srt(audio_file):
    stt_result = stt_process(audio_file)
    base_name = os.path.splitext(audio_file)[0]
    timestamp = int(time.time())
    output_file = f"{base_name}_{timestamp}.stt.srt"
    generate_srt(stt_result, output_file)
    return output_file


if __name__ == "__main__":
    audio_file = "path/to/your/audio/file.mp3"
    srt_file = process_audio_to_srt(audio_file)
    print(f"SRT file generated: {srt_file}")
