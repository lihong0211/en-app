from mitmproxy import http
from rich import print as rprint
import json
import subprocess
import os
from db import db

# 目标API接口
TARGET_API = "https://fanyi.baidu.com/client/translate/word"


def run_monitor():
    """
    启动 mitmdump 进程（在前台运行）
    """
    script_path = os.path.abspath(__file__)
    cmd = [
        "mitmdump",
        "--set",
        "upstream_cert=false",
        "--ssl-insecure",
        "-p",
        "6124",
        "-s",
        script_path,
    ]

    print(f"启动 mitmdump: {' '.join(cmd)}")
    # 在前台运行，不捕获输出
    process = subprocess.Popen(cmd)
    return process


def response(flow: http.HTTPFlow):
    """
    处理响应，构建结构化翻译结果对象
    """
    if flow.request.url.startswith(TARGET_API) and flow.response.content:
        try:
            # 解析主响应
            response_data = json.loads(flow.response.content.decode("utf-8"))
            result_str = response_data.get("data", {}).get("result")

            if result_str:
                # 解析result字段中的JSON
                result_data = json.loads(result_str)

                # 构建结构化对象
                translation_result = {
                    "word": result_data.get("src", ""),
                    "meaning": [],
                    "pronunciation": {},
                }

                # 提取释义信息
                for content_item in result_data.get("content", []):
                    for mean_item in content_item.get("mean", []):
                        meaning_type = mean_item.get("pre", "")
                        cont_dict = mean_item.get("cont", {})

                        if cont_dict:
                            # 将所有释义内容合并为一个字符串
                            meanings_list = list(cont_dict.keys())
                            meaning_content = ";".join(meanings_list)

                            translation_result["meaning"].append(
                                {"type": meaning_type, "content": meaning_content}
                            )

                # 提取发音信息
                for voice_item in result_data.get("voice", []):
                    if "en_phonic" in voice_item:
                        translation_result["pronunciation"]["en"] = voice_item[
                            "en_phonic"
                        ]
                    if "us_phonic" in voice_item:
                        translation_result["pronunciation"]["us"] = voice_item[
                            "us_phonic"
                        ]
                rprint(translation_result)
                return translation_result
            return None

        except json.JSONDecodeError as e:
            print(f"[错误] JSON解析失败: {e}")
            return None
        except Exception as e:
            print(f"[错误] 处理响应时出错: {e}")
            return None
    return None
