# 開発規約

## 1. 開発言語

本プロジェクトにおける開発言語の方針は、以下のとおりとする。

| 開発対象 | 言語 | 備考 |
| --- | --- | --- |
| クラウド環境 | Terraform | - 主に IaC (Infrastructure as Code) の構築・管理に利用する。<br>- バージョンは Terraform 1.10 系を推奨する。（2025年1月現在） |
| Cloud Run | Python | - 基本的には Python を採用する。<br>- 事情（例: サンプル実装が TypeScript で書かれており、TS の方が効率が良い場合など）がある場合は TypeScript でも可。<br>- オーナーとディベロッパー間で合意をとること。 |

---

## 2. レポジトリ内のレイアウト

レポジトリを単独プロジェクトごとに分割するか、monorepo でまとめるかは現状統一されていないため、個々の判断とする。

以下では、**単独プロジェクト**のレポジトリを仮定した場合のルートディレクトリ配下のレイアウトを想定して記述する。

```
┬─ (プロジェクトルート)
├─ terraform/
│   ├─ environments/
│   ├─ modules/
│   └─ ... (必要に応じて追加)
├─ python/
│   ├─ src/
│   ├─ tests/
│   ├─ requirements.txt
│   └─ ...
├─ docs/
│   └─ (ドキュメント類や draw.io 図表ファイルなど)
├─ .github/
│   └─ workflows/ (CI/CD 用ワークフロー)
└─ ...

```

- `terraform/`: インフラ構築用の Terraform コードを配置
    - `environments/`: ステージング/本番等、環境ごとの設定
    - `modules/`: 再利用可能なモジュール（ネットワークや Cloud Run、Cloud SQL などの単位モジュール）
- `python/`: アプリケーションコード・テストコードなどを配置
- `docs/`: ドキュメントや図表ファイルを配置
- `.github/workflows/`: GitHub Actions の定義（必要に応じて追加）

上記はあくまで一例であり、プロジェクトに合わせて柔軟に変更してよい。

---

## 3. Terraform

Terraform を用いた IaC を行う際の基本的な運用例を示す。実際の運用ではチームの規模やプロジェクトの特性に応じて調整する。

1. **バージョン管理**
    - `terraform/` ディレクトリ直下に `versions.tf` などを配置し、Terraform のバージョンを固定する。
    - `terraform.lock.hcl` ファイルをコミットし、チーム全体で同一バージョンを利用できるようにする。
2. **ディレクトリ構成**
    - `environments/` にステージングや本番など環境別の実行ファイル (`main.tf` など) を配置。
    - `modules/` に共通利用できるモジュールを配置し、環境ごとに参照して再利用性を高める。
3. **リソースの命名規則**
    - リソース名や変数名は、チーム内で統一したプレフィックス・サフィックスを付与するなど、一貫性を保つ。
4. **テスト**
    - 後述の[「テスト方針 > Terraform」](https://www.notion.so/17bfb2e35c9c80b0b304d890bef7dfa8?pvs=21) を参照。
5. **レビュー**
    - PR ベースでレビューを行い、State 破壊やリソース削除のリスクを最小限に抑える。
    - コンポーネントの追加/変更内容が影響しうる範囲を事前に周知し、レビューを依頼する。

---

## 4. Python

Python ディレクトリの基本方針を以下に示す。

なお、本ガイドラインはあくまで推奨であり、厳密な準拠を強制するものではない。各プロジェクトの要件に応じて柔軟に取捨選択する。

### ディレクトリ例

```
python/
├─ src/
│   └─ (アプリケーション本体)
├─ tests/
│   └─ (ユニットテスト・統合テスト等)
├─ pyproject.toml
└─ poetry.lock

```

- `src/`
    - アプリケーションのメインロジックを配置
    - `main.py` などのエントリーポイントを配置する場合もある
- `tests/`
    - 単体テスト（Unit test）、統合テスト（Integration test）等を配置
    - テストフレームワークは `pytest` や `unittest` を推奨
- Poetry を用いて依存関係を管理し、pyproject.toml および poetry.lock をコミットする。

### Python コードスタイル

- PEP8 に準拠したコーディングスタイルを推奨
- Linter, Formatter として `Ruff`  を推奨
- Github Actionsにlintを導入する際も上記を推奨

### その他

- 「早すぎる最適化」を避けるため、必要最低限のディレクトリ構成から始める
- 各種ユースケースに応じて必要が生じたタイミングでディレクトリを追加する

---

## 5. ブランチ・コミットメッセージ

### フローについて

- 複雑なブランチ運用は避けたいので、シンプルかつ柔軟な **GitHub Flow** をベースにする。
    1. `main` ブランチからトピックブランチを切る
    2. 作業後、Pull Request (PR) を作成
    3. レビューの後 `main` ブランチへマージ

### prefix

- 以下を基本とし、必要に応じて追加検討する。

| prefix | description |
| --- | --- |
| feat | 機能開発 |
| docs | ドキュメントの変更 |
| fix | バグフィックス |
| test | テスト関連 |
| refactor | リファクタリング |
| chore | その他雑用（依存関係の更新など） |

### ブランチ名

- 以下のいずれかの形式で命名する
1. `prefix/{issue ID}`
    - 例) `feat/123`
2. `prefix/{対応内容を端的にkebab-caseで}`
    - 例) `fix/foo-bar-baz`

### コミットメッセージ

- **Conventional Commits** にゆるく準拠する。
- 1 行目は以下に従って書く。

```
# 書式例
prefix: 対応内容を端的に書く(日本語OK)

# 例
feat: いい感じの機能を追加

# モノレポの場合はscopeを加える
test(certification_version/src/gui): いい感じのテストを追加

```

- 参考: [Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)

---

## 6. Gitタグ

将来のリリースに備える、あるいはテスト完了時点を明確にするなどの意図で、チェックポイントとなるコミットに対して **Git タグ** をアタッチすることを推奨する。

- **セマンティックバージョニング** を用いる。
    - `v<major>.<minor>.<patch>` の形式
    - 例) `v1.0.0`, `v1.1.0`, `v1.1.1`

---

## 7. テスト方針

### 7.1 Terraform

Terraform におけるテストの一例として、以下を参考にする。

- **Lint / Format チェック**
    - `terraform fmt -check` や `terraform validate` を使い、コードの構文エラーやフォーマット崩れを検出。
- **ユニットテスト的な考え方**
    - [terraform-compliance](https://github.com/terraform-compliance/terraform-compliance) などのツールを利用し、ポリシー違反や設定不備を早期に検知。
    - 主要なモジュールについては単体モジュールテストを検討する。
- **結合テスト（Integration test）**
    - 実際に Terraform を適用し、リソースが期待通りに作られるか、依存関係が正しく設定されているかを確認。
    - 検証環境を活用し、State の内容やリソースの稼働状況を確認する。

### 7.2 Cloud Run 等のアプリケーション

### ■ テスト全体像

（なんか作図する？）

### ■ テストの分類

| 種別 | 目的 | やり方 | 具体例 |
| --- | --- | --- | --- |
| Unit test | 機能要件に従って、コードが正しく動くことを保証する | - 本物のリソースは使わず Mock や Fake を利用してローカルで完結。 | 未整備 |
| Integration test | 機能要件に従って、本物のリソースが正しく動くことを保証する | - 実際に Google Cloud 等に接続して、本物リソースを利用してテスト。 | 未整備 |
| System test | ユーザ目線でシステム全体が正しく動くことを保証する | - Google Cloud などの環境にデプロイした状態で、実際のユーザー操作を想定してテスト | 未整備 |
- 開発エピック毎にテスト計画を立て、オーナーと合意すること
- 非機能要件（監視や性能など）についても必要に応じてテストを実施
- **Integration test**・**System test** は自動化しづらく、テスト数が増えると工数も増大する。Unit test を充実させ、これら大がかりなテストの回数・範囲をなるべく減らすことを推奨

### ■ TIPS

- **正常系・準正常系・異常系テスト** の考え方
    - 正常系: 設計されたアプリケーションの正常機能が正しく動作するか
    - 準正常系: 設計された例外処理が正しく動作するか
    - 異常系: 設計の想定外に対してアプリケーションがどのように動作するか
- **Mock と Fake**
    - Mock: クラウド SDK 等の振る舞いをテストライブラリなどでモック化してテスト
    - Fake: 本物の代わりに、ほぼ同等の動作をする疑似リソースを利用してテスト
    - Mock と Fake は排他的ではなく、同時使用も考えられる
    - Fake しにくいリソース（IAM、VPC など）は実際に作成して動作を確認する
- テストダブルに関しては以下を参考
    - [https://martinfowler.com/bliki/TestDouble.html](https://martinfowler.com/bliki/TestDouble.html)
    - [https://dev.classmethod.jp/articles/lambda-test-technology-sharing-meeting/](https://dev.classmethod.jp/articles/lambda-test-technology-sharing-meeting/)

---

## 8. コードレビュー

### 8.1 レビューコメント

レビューを円滑に進めるため、コメントの先頭に以下のようなラベルを付与することを推奨する。

| ラベル | 意味 | Approveブロック | 備考 |
| --- | --- | --- | --- |
| must | 必ず対応してほしい。対応するまで Approve 出来ない。 | Yes | ルール違反や重大なバグなど |
| imo | 個人的には対応した方が良いと考えている。 | No | レビュイーはなるべく対応を検討。対応しない場合は理由をコメントに残す |
| nits | 些細な指摘。 | No | コーディングスタイルやソート順など |
| q | 質問。回答をもらうまで Approve 出来ない。 | Yes | 指摘ではなく、疑問点や確認事項 |
| fyi | 情報共有のためのコメント。対応は不要。 | No | 参考リンクやドキュメントの案内など |

---

## 9. 作図ツール

- [**draw.io**](http://draw.io/) を利用する
    - `xml` ファイル ([draw.io](http://draw.io/) 形式) を Git リポジトリに含める
    - 作図の履歴も残すため、バイナリ書き出しのみでなく元の `xml` もコミットする
- 編集手段は自由
    - ブラウザ上の Web アプリ、Chrome Apps、VSCode Extension（非公式）など
- 作図結果の保存先は、各組織の情報システム利用ガイドラインに反しない場所を選択する
    - 顧客との共有ディレクトリがある場合はそちらを優先活用

---

## 10. 外部サービスとの連携について

### 10.1 Slack

- 主に外部ステークホルダーとのコミュニケーションに利用する
- PR/Issue などの更新情報を通知する専用チャンネルを設置してもよい
- 機微な情報（APIキーやパスワードなど）を投稿しないよう注意する
- Bot やアプリ連携を行う場合は権限管理に留意する

### 10.2 Discord

- 主に社内でのコミュニケーションに利用する
- Slack 同様に通知チャンネルを設置したり、外部ツール連携を行うこともできる
- 雑談やアイデア出しなど、カジュアルなコミュニケーションで活用する

---

## 11. クラウド環境名の命名について

GCP や他クラウドのリソースを作成する際に、環境ごと・目的ごとに一貫した命名規則を適用する

- 例:
    - **プロジェクトID**: `{組織名}-{サービス名}-{環境}`
        - 例) `acme-fooapp-dev` / `acme-fooapp-prod`
    - **サービスアカウント**: `sa-{機能名}@{プロジェクトID}.iam.gserviceaccount.com`
    - **Cloud Storage バケット**: `gs://{プロジェクトID}-{用途}-bucket`
- 大文字/アンダースコア/ハイフンなどの使用ルールをチーム内で統一しておく
- Terraform から作成する場合は変数化する

---

## 12. Cloud Run 内部のアーキテクチャについて

Cloud Run 上でアプリケーションを動かす際の一般的なアーキテクチャ例を示す。

- **ディレクトリ構成**
    - Python アプリの場合は `python/src/` や `python/app/` フォルダをベースにビジネスロジックを配置
    - `Dockerfile` をレポジトリに含め、ビルド手順や依存関係を明示
- **設定**
    - リクエスト数・CPU 使用量などに基づく自動スケーリングを利用
    - Cloud SQL など他サービスと連携する際は [Cloud SQL Proxy](https://cloud.google.com/sql/docs/mysql/connect-run) の活用を検討
- **セキュリティ**
    - Cloud Run の [サービスアカウント](https://cloud.google.com/run/docs/configuring/service-accounts) を適切に設定
    - HTTPS（SSL）を強制する
    - プライベートな Cloud Run (VPC Connector 経由) にする場合は VPC 設計も検討
- **ログ/モニタリング**
    - Cloud Logging や Cloud Monitoring を使い、Runtime のメトリクスやログを一元管理

---

## 13. 開発時の推奨行動

### 13.1 基本思想

特にコーディングが関係するタスクを念頭に記載する。

基本的な行動指針は、小刻みに仮説を立て、検証するサイクルを回すこと。

不確かな・不確実なことが、少しでも時間軸的に早く露呈するような動き方・コミュニケーションを推奨する。

1. **早期対話の重視**
    - 定期イベント(例: スプリントレビューや定例MTG)を待たずに、疑問点・新情報があれば速やかに議論する
2. **段階的な「作るべきモノ」の明確化**
    - 一度の検討ですべてが固まることは稀。仮説検証やプロトタイピングを繰り返し、像を鮮明にする
3. **発見された「失敗」や「不都合」は歓迎**
    - ただし、発見までのリードタイムが長い場合は、改善の余地あり（より小刻みに検証・レビューできなかったかを振り返る）
4. **抽象度の高い部分の認識合わせを重視**
    - Why, What を取り違えると被害が大きい。こまめに認識をすり合わせる

### 13.2 行動基準

やや大きめの単位（1 スプリントより長い場合もある）の仕事、すなわち **エピック** を念頭にした行動基準の例。

1. **「問題」に対する理解・認識を自分の言葉で復唱**
    - 図や疑似コードを使ったデモ、目的や問題意識をまとめた資料などを作成し、共有する
    - 入力情報を受け取るだけでなく、必ず自分なりにアウトプットして、噛み砕いた理解をぶつける
2. **詳細仕様・実装に入る前の「抽象度の高い相談」を早めに**
    - レビュー依頼や PR オープンの段階ではすでに具体化されすぎている場合が多い
    - 事前に抽象的な課題感や大まかな設計方針だけでも共有しておくと、より良い設計に繋がる可能性が高まる
3. **ドラフト実装による早期検証**
    - 書き捨て前提のドラフトコードを作り、他者へ見せる
    - 副次的な要素（エラーハンドリングやインフラ細部）は飛ばし、本質のロジックに集中
    - 「どうすれば動くのか」不確実な状態を早めに解消し、本質的な設計・実装検討に時間を使う

---

## 14. Selenium（Python）

### 14.1 Selenium（Python） コードスタイル

- [PEP8](https://peps.python.org/pep-0008/) に準拠し、`Ruff` などの Linter/Formatter を導入することを推奨
- 取得対象や操作対象を分かりやすくするため、適宜コメントや docstring を記述

### 14.2 ディレクトリ構成例

```
python/
├─ src/
│   ├─ main.py
│   └─ scraper/
│       ├─ base.py
│       ├─ example_site_scraper.py
│       └─ ...
├─ tests/
│   ├─ unit/
│   ├─ integration/
│   └─ e2e/
└─ ...

```

- `scraper/` ディレクトリにスクレイピングロジックをまとめる
- サイトごとにクラスや関数を分け、保守しやすい単位で管理

### 14.3 ライブラリ・依存管理

- Selenium (`selenium` パッケージ)
- WebDriver Manager ([webdriver_manager](https://pypi.org/project/webdriver-manager/))
- これらを `pyproject.toml` (Poetry) などでバージョン管理してチーム内で統一する

### 14.4 スクレイピング実装ガイドライン

1. **ブラウザ起動と終了**
    - 処理後は `driver.quit()` などで明示的に終了
2. **待機の設定**
    - ページ切り替えや JavaScript の読み込みがある場合は `WebDriverWait` を活用
3. **HTML 要素の取得**
    - `find_element()` や `find_elements()` で安定したセレクタを使用
4. **DOM 操作・画面遷移**
    - ログインやフォーム送信などのステップ操作を想定
5. **例外処理**
    - `NoSuchElementException` や `TimeoutException` などの例外を捕捉し、適切にログ出力

### 14.5 ログ出力と Cloud Logging

- **スクレイピング結果や進捗を把握するため**、状況をログで出力する
- ローカル環境で Selenium を動かす場合も、**Cloud Logging** への送信を推奨
    - 例: Google Cloud Python ライブラリを導入し、実行時に Cloud Logging へ転送

### 14.6 スクレイピングと CI/CD

- **CI（Lint・テスト）**
    - スクレイパー単体のユニットテストを行う場合、Mock やダミー HTML でテストする
- **CD（デプロイ・定期実行）**
    - Docker コンテナ化して定期実行する場合、Google Cloud Run や GitHub Actions のスケジュール機能などを活用
    - Secrets (ログイン情報など) は GitHub Secrets や Google Cloud の Secret Manager 等で安全に管理

### 14.7 セキュリティとリスク管理

- **認証情報**
    - パスワードやトークンは Git に平文でコミットせず、Secrets などで管理
- **利用規約**
    - 対象サイトの利用規約や robots.txt を確認
- **ログインが必要なページ**
    - 大量取得や自動ログインが規約で禁止されていないか事前に確認

---

## 15. GitHub Actions を用いた CI/CD 規約

本プロジェクトでは、GitHub Actions を用いてコードの品質維持・自動デプロイを行う場合の基本的な規約を示す。

### 15.1 目的

- **品質向上**
    - テストや Lint を自動で実行し、コードの問題を早期に検知
- **デプロイ自動化**
    - Terraform や Docker イメージのビルド・デプロイなどを PR マージやタグ発行等のイベントと連動させる
- **一貫性確保**
    - ローカル環境の違いに依存せず、同じ手順・条件でビルド/テスト/デプロイが行われる

### 15.2 ディレクトリ構成

既存の記述と重複しますが、再掲します。

```
(プロジェクトルート)/
├─ .github/
│   └─ workflows/
│       ├─ ci.yaml
│       ├─ cd.yaml
│       └─ etc...
├─ terraform/
├─ python/
└─ ...

```

- `.github/workflows/` 以下に CI/CD 用のワークフローファイル（YAML）を配置する
- `ci.yaml` : Lint、テストなどを行うためのワークフロー
- `cd.yaml` : デプロイ作業を行うためのワークフロー
- 必要に応じてファイルを分割し、処理を見通し良くする

### 15.3 シークレットと環境変数

- 機密情報（API キー、サービスアカウント JSON、認証トークンなど）は **GitHub のリポジトリ/Org Secret** を利用して安全に管理する
- 環境固有の変数は `.env` ファイルや Workflow ファイル内に記述する場合がある
    - **Secret ではない**がビルド時に必要な設定値（例: RUNTIME=python3.11 など）は Actions 内で明記するか、適切に管理する

### 15.4 ワークフロー例

### 15.4.1 CI（テスト・Lint）ワークフロー

```yaml
name: CI

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Lint
        run: |
          poetry run ruff python/

      - name: Test
        run: |
          poetry run pytest python/tests

```

- Pull Request の作成/更新時、および `main` ブランチへのプッシュ時に Lint やテストを実行
- Python バージョンは `3.11` を例示しているが、必要に応じて複数バージョンをテストする

### 15.4 注意事項

1. **ワークフローが複雑化しすぎないように**
    - 小さめの単位でファイルを分割し、職責をはっきりさせる (CI 用 / CD 用 など)
2. **排他制御・並列実行**
    - Terraform 適用を並列で走らせると State ファイルの整合性が崩れる恐れがある
    - `needs` キーワードや Terraform Cloud を活用するなど、衝突を防ぐ仕組みを検討する
3. **依存ライブラリのバージョン固定**
    - Python, Terraform, Node.js などを組み合わせる場合、それぞれバージョンを固定しチームで揃えること
4. **Secrets の管理**
    - 誤ってログ出力などで Secrets が露出しないように、プルリクレビューやローカルテストの段階で十分にチェックする

---
