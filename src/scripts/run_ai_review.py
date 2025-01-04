# ファイル例: scripts/run_ai_review.py

import os
import json
import subprocess

from openai import OpenAI
import requests

def main():
    # 1. 環境変数の取得
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY が設定されていません。")
        return

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN が設定されていません。")
        return

    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("Error: GITHUB_REPOSITORY が設定されていません。")
        return

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.isfile(event_path):
        print("Error: GITHUB_EVENT_PATH が無効です。")
        return

    # 2. OpenAI APIキーのセット
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 3. baseブランチ(main) を fetch し、base...HEAD の差分を取得
    #    ※ baseブランチが "main" ではない場合は適宜変更
    subprocess.run(["git", "fetch", "origin", "main"], check=True)

    diff_result = subprocess.run(
        ["git", "diff", "origin/main...HEAD"], 
        capture_output=True, 
        text=True
    )
    diff_text = diff_result.stdout

    if not diff_text.strip():
        print("差分がないのでコードレビューできません。")
        return

    # 4. OpenAIへレビュー依頼
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # 例: "gpt-3.5-turbo" や "gpt-4" など
            messages=[
                {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
                {
                    "role": "user",
                    "content": f"以下のdiffをレビューして、問題点や改善提案をコメント用に出力してください。\n{diff_text}"
                },
            ],
        )
    except Exception as e:
        print(f"OpenAI API へのリクエストでエラーが発生しました: {e}")
        return

    # ChatCompletion のレスポンスを取り出す
    try:
        review_comment = response.choices[0].message.content
    except (IndexError, KeyError) as e:
        print(f"ChatCompletion のレスポンスが想定外の形式です: {e}")
        return

    # 5. pull_request の情報を event_path から取得
    with open(event_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "pull_request" not in payload:
        print("このイベントは pull_request ではありません。")
        return

    pr_number = payload["pull_request"].get("number")
    if not pr_number:
        print("PR番号が取得できませんでした。")
        return

    # 6. PR へコメント投稿
    post_comment_to_pr(repo, pr_number, review_comment, GITHUB_TOKEN)


def post_comment_to_pr(repo, pr_number, body, token):
    """
    指定したリポジトリ/PR番号に対して body の内容をコメント投稿する。
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": body}

    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        print("コメント投稿成功です！")
    else:
        print(f"コメント投稿失敗です…ステータスコード: {resp.status_code}")
        print(resp.text)


if __name__ == "__main__":
    main()
