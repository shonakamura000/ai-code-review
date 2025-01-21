# scripts/run_ai_review.py

import os
import json
import subprocess
from pathlib import Path
import requests
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI as LlamaOpenAI
import re

# 定数の定義
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "prompts/code_review_prompt.md"
PROMPT_CLASSIFICATION_PATH = PROJECT_ROOT / "prompts/classification_prompt.md"
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
    pattern = r"^diff --git a/(.+?) b/\1"
    lines = diff_text.splitlines()
    
    current_file = None
    current_lines = []
    
    for line in lines:
        if line.startswith("diff --git a/"):
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

def generate_review(client, prompt):
    """
    レビュー内容を生成する関数
    """
    try:
        review_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=800,
        )
        print(f"review_response:\n{review_response}")
        content = review_response.choices[0].message.content.strip()
        # トークン数の表示
        if hasattr(review_response, "usage"):
            usage_info = review_response.usage
            print(f"Prompt Tokens: {usage_info.prompt_tokens}, "
                  f"Completion Tokens: {usage_info.completion_tokens}, "
                  f"Total Tokens: {usage_info.total_tokens}")
        print(f"content: {content}")
        return content
    except Exception as e:
        print(f"レビュー生成中にエラーが発生しました: {e}")
        return "レビューの生成に失敗しました。"
    

def determine_action(client, review_content):
    """
    レビュー内容を基にアクションを判断する関数
    """
    try:
        action_prompt = load_file(PROMPT_CLASSIFICATION_PATH).format(review_content=review_content)

        action_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
                {"role": "user", "content": action_prompt},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        print(f"action_response:\n{action_response}")
        action_content = action_response.choices[0].message.content.strip()

        # トークン数の表示
        if hasattr(action_response, "usage"):
            usage_info = action_response.usage
            print(f"Prompt Tokens: {usage_info.prompt_tokens}, "
                  f"Completion Tokens: {usage_info.completion_tokens}, "
                  f"Total Tokens: {usage_info.total_tokens}")

        return action_content
    except Exception as e:
        print(f"アクション判定中にエラーが発生しました: {e}")
        return "Comment"

def filter_diff_lines(diff_text):
    filtered_lines = []
    for line in diff_text.splitlines():
        # 行番号表示は残す場合
        if line.startswith("@@"):
            filtered_lines.append(line)
            continue
        if line.startswith("-"):
            # 削除行は除外
            continue
        # 追加行('+')か、文脈行(' ')かは残す
        filtered_lines.append(line)
    return "\n".join(filtered_lines)

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

    # mainブランチの最新をfetch
    subprocess.run(["git", "fetch", "origin", "main"], check=True)

    # diff取得時にコンテキスト行を増やす (--unified=10 なら前後10行)
    # Uオプションを増やせば増やすほど周辺行数が多くなるで
    diff_result = subprocess.run(
        ["git", "diff", "origin/main...HEAD", "--unified=10"],
        capture_output=True, text=True
    )
    raw_diff_text = diff_result.stdout.strip()
    print(f"raw_diff_text:{raw_diff_text}")

    if not raw_diff_text:
        print("差分がないためレビューできません。")
        return

    # フィルタリングして削除行(-)は除外
    filtered_diff_text = filter_diff_lines(raw_diff_text)

    # ファイル単位に分割
    file_diff_map = split_diff_by_file(filtered_diff_text)
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

    # LLMの設定
    Settings.llm = LlamaOpenAI(api_key=OPENAI_API_KEY, temperature=0.0)
    Settings.chunk_size = 1024
    query_engine = index.as_query_engine()

    file_guidelines_map = {}
    file_reviews_map = {}

    # ファイルごとにガイドライン検索＋レビュー生成
    for filename, filediff in file_diff_map.items():
        query = (
            f"以下はファイル '{filename}' の差分です。"
            "これに関連するコードガイドラインを **日本語で** 教えてください:\n"
            f"{filediff}"
        )
        try:
            response = query_engine.query(query)
            retrieved_guidelines = str(response)
            file_guidelines_map[filename] = retrieved_guidelines

            prompt = prompt_template.format(
                diff_text=filediff,
                code_guidelines=retrieved_guidelines
            )
            file_review = generate_review(client, prompt)
            file_reviews_map[filename] = file_review

        except Exception as e:
            print(f"LlamaIndex クエリ中にエラーが発生しました: {e}")
            file_guidelines_map[filename] = "ガイドライン取得に失敗しました"
            file_reviews_map[filename] = "レビュー生成に失敗しました"

    review_content = "Nakamura Code Rabbitによるコードレビュー\n# 問題点と修正点\n"
    for filename, review_text in file_reviews_map.items():
        review_content += f"\n### {filename}\n{review_text}\n"

    action = determine_action(client, review_content)
    print(f"アクション: {action}\nレビュー内容: {review_content}")

    with open(event_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "pull_request" not in payload:
        print("このイベントは pull_request ではありません。")
        return

    pr_number = payload["pull_request"].get("number")
    if not pr_number:
        print("PR番号が取得できません。")
        return

    # 判定結果に応じてPRに反映
    if action == "Comment":
        post_comment_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)
    elif action == "Approve":
        approve_pr(repo, pr_number, GITHUB_TOKEN)
        post_comment_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)
    elif action == "Request changes":
        request_changes_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)
    else:
        post_comment_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)

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