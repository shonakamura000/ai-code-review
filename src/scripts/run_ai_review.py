# scripts/run_ai_review.py

import os
import json
import subprocess
from pathlib import Path
import requests
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.query_engine import QueryEngine
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

import re

# 定数の定義
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "prompts/code_review_prompt.md"
GUIDELINES_PATH = PROJECT_ROOT / "doc/code-guidelines.md"
INDEX_PATH = PROJECT_ROOT / "indexes"

def load_file(file_path):
    """
    ファイルを読み込む汎用関数
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        return None

def load_index():
    """
    LlamaIndex のインデックスをロードする関数
    """
    try:
        storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_PATH))
        index = load_index_from_storage(storage_context)
        print("LlamaIndex のインデックスをロードしました。")
        return index
    except Exception as e:
        print(f"インデックスのロード中にエラーが発生しました: {e}")
        return None

def split_diff_by_file(diff_text):
    """
    git diff テキストをファイル単位に分割して返す関数。
    戻り値は {ファイルパス: そのファイルのdiff} の辞書を想定。
    """
    file_diffs = {}
    # diffセパレータっぽい正規表現で分割する
    # 例: diff --git a/path/to/file b/path/to/file
    pattern = r"^diff --git a/(.+?) b/\1"
    lines = diff_text.splitlines()
    
    current_file = None
    current_lines = []
    
    for line in lines:
        if line.startswith("diff --git a/"):
            # 新しいファイルdiffの開始
            # これまでのファイルを登録
            if current_file and current_lines:
                file_diffs[current_file] = "\n".join(current_lines)
            match = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
            if match:
                filename = match.group(1)
                current_file = filename
                current_lines = [line]
            else:
                current_file = None
                current_lines = []
        else:
            if current_file is not None:
                current_lines.append(line)

    # 最後のファイルを登録
    if current_file and current_lines:
        file_diffs[current_file] = "\n".join(current_lines)

    return file_diffs

def main():
    # 環境変数と設定の取得
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not all([OPENAI_API_KEY, GITHUB_TOKEN, repo, event_path]):
        print("必要な環境変数が設定されていません。")
        return

    # OpenAI クライアントの設定
    client = OpenAI(api_key=OPENAI_API_KEY)

    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    diff_result = subprocess.run(
        ["git", "diff", "origin/main...HEAD"], capture_output=True, text=True
    )
    diff_text = diff_result.stdout.strip()

    if not diff_text:
        print("差分がないためレビューできません。")
        return
    print(f"diff_text:\n{diff_text[:1000]}...") 

    # diffをファイル単位に分割
    file_diff_map = split_diff_by_file(diff_text)
    if not file_diff_map:
        print("ファイル単位のdiffに分割できませんでした。")
        return

    # プロンプトテンプレートの読み込み
    prompt_template = load_file(PROMPT_TEMPLATE_PATH)
    if not prompt_template:
        return
    print(f"prompt_template:\n{prompt_template}")

    # LlamaIndex のインデックスをロード
    index = load_index()
    if not index:
        return

    # LLMまわりの設定
    Settings.llm = OpenAI(api_key=OPENAI_API_KEY, temperature=0.0)
    Settings.chunk_size = 1024

    query_engine = index.as_query_engine()

    # ファイルごとに関連するガイドラインを取得して、結果をまとめる
    file_guidelines_map = {}

    for filename, filediff in file_diff_map.items():
        # ファイルの差分をRAGにかける
        query = (
            f"以下はファイル '{filename}' の差分です。"
            "これに関連するコードガイドラインを教えてください:\n"
            f"{filediff}"
        )
        try:
            response = query_engine.query(query)
            retrieved_guidelines = str(response)
            file_guidelines_map[filename] = retrieved_guidelines
        except Exception as e:
            print(f"LlamaIndex クエリ中にエラーが発生しました: {e}")
            file_guidelines_map[filename] = "ガイドライン取得に失敗しました"

    # ファイルごとのガイドライン情報をまとめて1つのコメントにする
    combined_guidelines = ""
    for filename, guidelines in file_guidelines_map.items():
        combined_guidelines += f"\n### {filename}\n{guidelines}\n"

    # プロンプトに差分全体や取得したコード規約を埋め込む
    # 今回はファイル単位のガイドライン結果をまとめたものを使う
    prompt = prompt_template.format(
        diff_text=diff_text[:2000] + "...(省略)",  
        code_guidelines=combined_guidelines
    )
    print(f"prompt:\n{prompt}")

    # OpenAI API 呼び出し
    try:
        review_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=800 
        )
        print(f"review_response:\n{review_response}")
    except Exception as e:
        print(f"OpenAI API 呼び出し中にエラーが発生しました: {e}")
        return

    # JSON パース
    try:
        content = review_response.choices[0].message.content.strip()
        review_json = json.loads(content)
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"API 応答を JSON として解釈できませんでした: {e}")
        print(f"応答内容: {review_response}")
        return

    # JSON に含まれる情報を取り出す
    action = review_json.get("action", "Comment")
    reason = review_json.get("reason", "理由が取得できませんでした。")

    # PR 情報取得
    with open(event_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "pull_request" not in payload:
        print("このイベントは pull_request ではありません。")
        return

    pr_number = payload["pull_request"].get("number")
    if not pr_number:
        print("PR番号が取得できません。")
        return

    # 判定したアクションに応じて GitHub に反映
    if action == "Comment":
        post_comment_to_pr(repo, pr_number, reason, GITHUB_TOKEN)
    elif action == "Approve":
        approve_pr(repo, pr_number, GITHUB_TOKEN)
        post_comment_to_pr(repo, pr_number, reason, GITHUB_TOKEN)
    elif action == "Request changes":
        request_changes_to_pr(repo, pr_number, reason, GITHUB_TOKEN)
    else:
        post_comment_to_pr(repo, pr_number, reason, GITHUB_TOKEN)

def post_comment_to_pr(repo, pr_number, body, token):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"body": body}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        print("コメント投稿成功！")
    else:
        print(f"コメント投稿失敗: {resp.status_code} - {resp.text}")

def approve_pr(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"event": "APPROVE"}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        print("PR承認成功！")
    else:
        print(f"PR承認失敗: {resp.status_code} - {resp.text}")

def request_changes_to_pr(repo, pr_number, body, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"body": body, "event": "REQUEST_CHANGES"}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        print("変更要求成功！")
    else:
        print(f"変更要求失敗: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    main()