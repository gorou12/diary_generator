# 本番デプロイ

## 概要

本番デプロイはGitHub Actionsから実行する。

```text
mainへpush
    |
    v
GitHub Actions
    |
    | SSH
    v
pokete1_vps2
/home/gorou12/diary_generator
    |
    +-- originをHTTPSへ正規化
    +-- git pull --ff-only origin main
    +-- uv sync
    +-- systemctl start diary-generator.service
            |
            +-- scripts.generate
            +-- rsync output/ -> /var/www/html/diary/
```

GitHub Actions workflowとアプリ側のデプロイスクリプトはこのリポジトリを正とする。

VPS側のsystemd / nginx / sudoers設定は `gorou12/pokete-network` を正とする。

## デプロイトリガー

Workflow:

```text
.github/workflows/main.yml
```

通常は `main` へのpushで自動デプロイする。

以下だけを変更したpushでは、自動デプロイを起動しない。

- `docs/**`
- `README.md`
- `.github/**`
- `scripts/deploy_vps.sh`

デプロイ基盤自体を変更しただけで、VPS側の準備が終わる前に新しいWorkflowが自動実行されるのを避けるため。

また `workflow_dispatch` に対応しているため、GitHub Actions画面から手動実行できる。
デプロイ設定を変更した直後の確認には手動実行を使う。

## GitHub Actions Secrets

このリポジトリには次のActions Secretsが必要。

- `VPS_HOST`
- `VPS_USER`
- `SSH_PRIVATE_KEY`

実値はGitへ保存しない。

`SSH_PRIVATE_KEY` はGitHub Actionsから本番VPSへ接続する秘密鍵。
対応する公開鍵をVPSの次のファイルへ登録する。

```text
/home/gorou12/.ssh/authorized_keys
```

VPS再構築時には安全なmigration backup等から秘密鍵をGitHub Actions Secretsへ復旧してよいが、秘密鍵をリポジトリやドキュメントへ保存しない。

## SSHは2経路ある

このデプロイではSSH/Git接続を混同しない。

### 1. GitHub Actions -> VPS

GitHub Actions Secretsの:

```text
SSH_PRIVATE_KEY
```

を使う。

この鍵が間違っている場合、VPSへのSSH接続そのものが失敗する。

### 2. VPS -> GitHub

VPS上のcheckoutを更新するための接続。

`diary_generator` はpublic repositoryなので、GitHubへのSSH鍵は使わずHTTPSでpullする。

Workflowでは毎回originを次へ正規化する。

```text
https://github.com/gorou12/diary_generator.git
```

そのためVPS上にGitHub用SSH秘密鍵は不要。

確認:

```bash
cd /home/gorou12/diary_generator
git remote -v
```

もし次のようになっていた場合:

```text
git@github.com:gorou12/diary_generator.git
```

手動で直す場合は:

```bash
git remote set-url origin https://github.com/gorou12/diary_generator.git
git remote -v
```

## VPS側の要件

VPSには次が必要。

- user: `gorou12`
- checkout: `/home/gorou12/diary_generator`
- uv: `/home/gorou12/.local/bin/uv`
- systemd unit: `diary-generator.service`
- publication directory: `/var/www/html/diary`
- passwordなしsudoを次の1コマンドに限定して許可
  - `/usr/bin/systemctl start diary-generator.service`

VPS側の詳細は:

```text
gorou12/pokete-network
docs/apps/diary-generator.md
config/host/systemd/
config/host/sudoers/
```

を参照。

## デプロイスクリプト

`scripts/deploy_vps.sh` はVPS上で `git pull` 後に実行する。

処理:

1. `uv sync`
2. `sudo -n /usr/bin/systemctl start diary-generator.service`

HTML生成とrsyncはこのスクリプトへ重複記載しない。
`pokete-network` で管理するsystemd serviceへ一本化する。

## systemdへ生成・公開処理を集約する理由

同じ処理を:

- 毎時timer
- GitHub Actions deploy
- 手動実行

から利用する。

生成・公開手順をsystemd unitへ集約することで、複数箇所でコマンド列が少しずつ違う状態を避ける。

実行ログはjournaldで確認する。

```bash
journalctl -u diary-generator.service -n 100 --no-pager
```

## 本番checkoutをきれいに作り直す

VPS上のcheckout自体がおかしい、origin設定や過去の作業痕跡をまとめて捨てたい場合に使う。

### 1. timerを一時停止

```bash
sudo systemctl stop diary-generator.timer
```

### 2. Git管理外データを退避

最低限 `.env` を退避する。

```bash
cd /home/gorou12

mkdir -p diary-generator-reinstall-backup
cp -a diary_generator/.env diary-generator-reinstall-backup/ 2>/dev/null || true
```

必要なら再取得時間短縮のため `cache/` も退避する。

```bash
cp -a diary_generator/cache diary-generator-reinstall-backup/ 2>/dev/null || true
```

`output/` は再生成できるため通常は不要。

### 3. 旧checkoutを退避

すぐ削除せず名前を変える。

```bash
mv diary_generator diary_generator.old
```

### 4. HTTPSでclone

```bash
git clone \
  https://github.com/gorou12/diary_generator.git \
  /home/gorou12/diary_generator
```

### 5. secret等を戻す

```bash
cp -a \
  /home/gorou12/diary-generator-reinstall-backup/.env \
  /home/gorou12/diary_generator/.env
```

cacheも退避した場合:

```bash
cp -a \
  /home/gorou12/diary-generator-reinstall-backup/cache \
  /home/gorou12/diary_generator/cache
```

### 6. 依存関係・生成を確認

```bash
cd /home/gorou12/diary_generator
/home/gorou12/.local/bin/uv sync

sudo -n /usr/bin/systemctl start diary-generator.service

journalctl \
  -u diary-generator.service \
  -n 100 \
  --no-pager
```

サイトも確認する。

### 7. timerを戻す

```bash
sudo systemctl start diary-generator.timer
systemctl status diary-generator.timer --no-pager
```

新checkoutで問題ないことを確認してから:

```text
/home/gorou12/diary_generator.old
/home/gorou12/diary-generator-reinstall-backup
```

を削除する。

## 手動本番テスト

VPS側の設定更新後、GitHubのActions画面から `Deploy to VPS` を手動実行する。

VPS側:

```bash
systemctl status diary-generator.timer --no-pager
journalctl -u diary-generator.service -n 100 --no-pager
```

を確認し、最後に公開サイトを確認する。

## トラブルシュート

### `git@github.com: Permission denied (publickey)`

GitHub ActionsからVPSへは接続できているが、VPS上のrepository originがSSH URLになっていると発生する。

次で修正する。

```bash
cd /home/gorou12/diary_generator

git remote set-url \
  origin \
  https://github.com/gorou12/diary_generator.git

git pull --ff-only origin main
```

このエラーだけなら、GitHub Actionsの `SSH_PRIVATE_KEY` を疑う必要はない。

秘密鍵そのものはトラブルシュート時にも表示・貼付しない。
