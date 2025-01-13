# ファイル例: scripts/run_ai_review.py

import os
import json
import subprocess

import requests
from openai import OpenAI


def load_prompt_template(file_path):
    """
    プロンプトテンプレートを外部ファイルから読み込む
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"プロンプトファイルが見つかりません: {file_path}")
        return None

def load_code_review_guidelines(file_path):
    """
    コードレビュー規約を外部ファイルから読み込む
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"コードレビュー規約ファイルが見つかりません: {file_path}")
        return None


def main():
    # 環境変数と設定の取得
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not all([OPENAI_API_KEY, GITHUB_TOKEN, repo, event_path]):
        print("必要な環境変数が設定されていません。")
        return

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # PR差分の取得
    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    diff_result = subprocess.run(
        ["git", "diff", "origin/main...HEAD"], capture_output=True, text=True
    )
    diff_text = diff_result.stdout.strip()

    if not diff_text:
        print("差分がないためレビューできません。")
        return

    # プロンプトテンプレートの読み込み
    prompt_template_path = "../prompts/code_review_prompt.md"
    prompt_template = load_prompt_template(prompt_template_path)
    if not prompt_template:
        return
    
    guidelines_path = "../prompts/code_review_guidelines.md"
    code_guidelines = load_code_review_guidelines(guidelines_path)

    # プロンプトに差分、コード規約を埋め込む
    prompt = prompt_template.format(diff_text=diff_text,code_tuidelines=code_guidelines)

    # OpenAI API呼び出し
    review_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens = 500
    )

    # JSONパース
    try:
        content = review_response.choices[0].message.content.strip()
        review_json = json.loads(content)
    except (IndexError, KeyError, json.JSONDecodeError):
        print("API応答をJSONとして解釈できませんでした。")
        return

    # JSONに含まれる情報を取り出す
    action = review_json.get("action", "Comment")
    reason = review_json.get("reason", "理由が取得できませんでした。")
    review_content = review_json.get("reviewContent", "レビュー内容が取得できませんでした。")

    # PR情報取得
    with open(event_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "pull_request" not in payload:
        print("このイベントは pull_request ではありません。")
        return

    pr_number = payload["pull_request"].get("number")
    if not pr_number:
        print("PR番号が取得できません。")
        return

    # 判定したアクションに応じてGitHubに反映
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
        print(f"コメント投稿失敗: {resp.status_code}")


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
        print(f"PR承認失敗: {resp.status_code}")


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
        print(f"変更要求失敗: {resp.status_code}")


if __name__ == "__main__":
    main()