# ファイル例: scripts/run_ai_review.py

import os
import json
import subprocess

from openai import OpenAI
import requests

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

    # OpenAIでレビュー分類を取得
    review_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
            {
                "role": "user",
                "content": f"以下のコード差分をレビューし、改善提案を以下の選択肢のどれかに基づいて分類してください：\n\n"
                           f"1. 'Comment': フィードバックを送信。\n"
                           f"2. 'Approve': 承認します。\n"
                           f"3. 'Request changes': 変更を要求します。\n\n"
                           f"コード差分:\n{diff_text}",
            },
        ],
    )

    review_action_raw = review_response.choices[0].message.content
    action = determine_action(review_action_raw)

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

    # レビュー内容の生成
    review_content = generate_review_content(openai_client, diff_text, action)

    # コメント投稿の分岐
    if action == "Comment":
        post_comment_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)
    elif action == "Approve":
        approve_pr(repo, pr_number, GITHUB_TOKEN)
        post_comment_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)
    elif action == "Request changes":
        request_changes_to_pr(repo, pr_number, review_content, GITHUB_TOKEN)


def generate_review_content(openai_client, diff_text, action):
    """
    アクションに応じてレビュー内容を生成
    """
    prompt = f"以下のコード差分を基に、{action}に対応する具体的なレビュー内容を生成してください。\n\nコード差分:\n{diff_text}"
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
            {"role": "user", "content": prompt},
        ],
    )
    try:
        return response.choices[0].message.content
    except (IndexError, KeyError):
        print("レビュー内容の生成に失敗しました。")
        return "レビュー内容の生成に失敗しました。"


def determine_action(comment):
    """
    OpenAIの応答からアクションを判定
    """
    if "承認します" in comment or "Approve" in comment:
        return "Approve"
    elif "変更を要求します" in comment or "Request changes" in comment:
        return "Request changes"
    return "Comment"


def post_comment_to_pr(repo, pr_number, body, token):
    """
    PRにコメントを投稿
    """
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
    """
    PRを承認
    """
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
    """
    PRに変更要求を送信
    """
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