# AI Code Review

このプロジェクトは、OpenAI APIを活用して、プルリクエストの差分を自動的にレビューするGitHub Actionsワークフローを提供します。

## 特徴
- OpenAIのGPTモデルを利用してコードレビューを実行
- プルリクエストの差分を解析し、コメントとしてGitHubに投稿

## 利用方法

1. **このリポジトリを公開ワークフローとして利用**
   自分のリポジトリで以下を設定してください。

   ```yaml
    name: Run AI Review

    on:
    pull_request:
        types: [opened, synchronize]

    permissions:
    contents: write
    pull-requests: write

    jobs:
    ai-review:
        uses: shonakamura000/ai-code-review/.github/workflows/ai_review_reusable.yml@main
        secrets:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
