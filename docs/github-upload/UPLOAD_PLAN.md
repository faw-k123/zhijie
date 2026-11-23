# 智解国音 GitHub 分批上传方案

## 1. 原则

本地文件不删除、不移动。Git仓库上传全部不可替代的项目内容，包括源码、80例研究数据、文档、数据库导出、图片、音频和视频。

以下内容保留在本地，但不进入仓库，因为可由清单重建或含本机状态：

- `backend/.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/.vite-cache/`
- `__pycache__/`、日志和真实 `.env`

## 2. 大文件策略

`.gitattributes` 已将 MP3、MP4、WAV、FLAC、M4A、MOV、AVI、SQL、DUMP 和 BAK 文件交给 Git LFS。普通Git只保存指针，大文件内容由Git LFS上传。

不要在第一次提交后才配置LFS，否则大文件会进入普通Git历史。

当前清单中约2.14GB媒体和约105MB数据库文件会主要占用LFS空间。GitHub Free目前包含10GiB LFS存储和每月10GiB下载流量，因此当前首次上传在额度范围内；反复修改并重新提交大文件会产生新的完整LFS对象，应避免无意义地重复提交音视频。

## 3. 初始化

在项目根目录执行：

```powershell
git init -b main
git lfs install --local
```

本目录已经准备了 `.gitignore`、`.gitattributes` 和分批脚本。

## 4. 生成批次清单

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\github\build-upload-manifest.ps1
```

生成：

- `docs/github-upload/file-manifest.csv`：每个文件所属批次、大小和LFS状态。
- `docs/github-upload/batch-summary.csv`：各批次文件数与总体积。

清单文件可以反复生成，不会修改或移动原文件。

## 5. 推荐提交顺序

每批遵循同一流程：暂存、检查、提交、推送。媒体批次由脚本自动控制在约350MB以内。

### 00-bootstrap

上传 `.gitignore`、`.gitattributes`、README、安装说明和上传脚本。

```powershell
.\scripts\github\stage-upload-batch.ps1 -Batch 00-bootstrap
git commit -m "chore: initialize repository and Git LFS"
git push -u origin main
```

### 01-core

上传前后端源码、配置模板和普通静态文件。

```powershell
.\scripts\github\stage-upload-batch.ps1 -Batch 01-core
git commit -m "feat: add application source code"
git push
```

### 02-research-docs

上传80例研究数据、候选案例、研究脚本、文档和答辩材料。

```powershell
.\scripts\github\stage-upload-batch.ps1 -Batch 02-research-docs
git commit -m "docs: add research data and project reports"
git push
```

### 03-database

上传数据库导出与初始化脚本。这些文件由Git LFS管理。

```powershell
.\scripts\github\stage-upload-batch.ps1 -Batch 03-database
git commit -m "data: add database initialization files"
git push
```

### media-01、media-02……

依次上传全部音频、视频和媒体辅助数据。以 `batch-summary.csv` 中实际生成的批次为准：

```powershell
.\scripts\github\stage-upload-batch.ps1 -Batch media-01
git commit -m "media: add asset batch 01"
git push
```

完成后继续 `media-02`，直至最后一个媒体批次。不要同时暂存多个媒体批次。

## 6. 创建GitHub远程仓库

在GitHub创建空仓库，不要预先添加README或 `.gitignore`。复制仓库地址后执行：

```powershell
git remote add origin https://github.com/你的用户名/zhijie-guoyin.git
git remote -v
```

建议在完成 `00-bootstrap` 后立即推送一次，再逐批上传。

## 7. 每批检查

暂存脚本执行后检查：

```powershell
git status --short
git diff --cached --stat
git lfs status
```

确认没有 `.env`、`.venv` 或 `node_modules` 后再提交。

## 8. 全部完成后的核验

```powershell
git status
git lfs ls-files
git log --oneline --decorate -12
```

另找一个空目录进行克隆验证：

```powershell
git clone https://github.com/你的用户名/zhijie-guoyin.git zhijie-guoyin-check
cd zhijie-guoyin-check
git lfs pull
```

按照 `作品安装说明.md` 安装依赖并启动前后端，重点检查音频、视频、80例案例库、国家因素和区域方案。

## 9. 失败处理

- 某批LFS上传中断：网络恢复后重新执行 `git push`。
- 普通Git提示单文件过大：检查 `.gitattributes`，运行 `git lfs status`，不要强行提交。
- 远程拒绝超过2GB的单次推送：确认一次只提交一个清单批次。
- 发现密钥：立即停止提交，从暂存区移除并更换密钥；不要仅在后续提交中删除。
