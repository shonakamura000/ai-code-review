## タスク
以下のコード差分をレビューしてください。
コード差分として、GitHubから取得したdiffを入力しています。そこからコードの変更後のコードに妥当性があるか判断してください

## 入力データ
### コード規約
{code_guidelines}

## コード差分
{diff_text}

## 注意事項
1. コード規約に厳密に従い、問題点を特定してください。
2. 修正案がある場合は具体的に提案してください（例: 「この関数名を xxx に変更することで可読性が向上します」など）。
3. レビューコメントは丁寧にまとめてください。
4. コメントはレビュー対象に含めないでください。コメント以外の部分に関してレビューしてください
5. レビューに関しては必ず日本語で行ってください。
6. 各レビューの際に、必ずどのコード規約を参照してコメントしているのか全文で記述してください

## 出力例
**コード規約**: 一貫性のある変数命名規則
   - 問題: 変数 `variableName` はキャメルケースで命名されていますが、コード規約ではスネークケースを使用することが求められています。
     - 修正案:
          ```python
               # 修正前
               variableName = \"value\"    
               # 修正提案
               variable_name = \"value\" 
          ```
