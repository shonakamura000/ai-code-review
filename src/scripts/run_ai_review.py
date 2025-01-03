# ファイル例: scripts/run_ai_review.py
import os
import requests
import openai
import subprocess

def main():
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # 差分を取得 (今回はGitHub Actions内やから直接 git diff で取得してみる)
    diff_result = subprocess.run(["git", "diff", "HEAD~1", "HEAD"], capture_output=True, text=True)
    diff_text = diff_result.stdout

    if not diff_text.strip():
        print("差分がないで。レビューする対象がないかもしれへん")
        return

    # AIで解析
    prompt = f"以下のdiffをレビューして、問題点や改善提案をコメント用に出力してや。\n{diff_text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは優秀なコードレビュアーです。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.2
    )
    review_comment = response.choices[0].message.content

    # GITHUB_REPOSITORY, GITHUB_EVENT_PATH なんかで環境変数から情報取れる
    repo = os.environ["GITHUB_REPOSITORY"]          # "ユーザ名/リポジトリ名"
    event_path = os.environ["GITHUB_EVENT_PATH"]    # pull_request情報がJSONで入っとるファイル

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = f.read()
    import json
    payload = json.loads(event_data)

    pr_number = payload["pull_request"]["number"]

    post_comment_to_pr(repo, pr_number, review_comment, github_token)

def post_comment_to_pr(repo, pr_number, body, token):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": body}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        print("コメント投稿成功やで！")
    else:
        print(f"コメント投稿失敗や…ステータスコード: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    main()