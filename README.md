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

   jobs:
     ai-review:
       uses: shonakamura000/ai-code-review/.github/workflows/ai_review.yml@main
       with:
         openai_api_key: ${{ secrets.OPENAI_API_KEY }}
         github_token: ${{ secrets.GITHUB_TOKEN }}
