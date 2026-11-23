# 智解国音

“智解国音”是面向中国传统音乐展示、情感分析与国际传播决策的 Web 应用。系统以 Vue 前端、Django 后端、SQL Server 与 Neo4j 为基础，整合传统音乐浏览、情感分析、国风意象解析、海外传播案例库、国家因素分析、区域传播方案和宣传内容生成等功能。

## 当前研究数据

- 国际传播案例：80例，全部进入案例展示、国家覆盖和描述性因素分析。
- 数据版本：`research/data/v1.8`。
- 因素编码：10项传播影响因素，共800条“案例×因素”记录；证据不足的项目保持空值。
- 候选音乐：20首，按歌曲独立生成传播主题、目标国家和案例参考。

## 技术结构

- 前端：Vue 3、TypeScript、Vite、ECharts、Three.js
- 后端：Django、Django REST Framework
- 数据库：Microsoft SQL Server、Neo4j
- 研究数据：版本化 JSON、CSV 与来源索引
- 大文件：音频、视频和数据库导出使用 Git LFS 管理

## 目录

```text
backend/       Django 后端、研究分析接口与媒体资源
frontend/      Vue 前端
db/            SQL Server 初始化及补充脚本
research/      国际传播案例、编码、来源与版本数据
docs/          研究报告、测试记录和答辩材料
scripts/       GitHub 分批上传辅助脚本
```

## 安装与启动

完整环境要求、数据库导入和启动步骤见 [作品安装说明.md](作品安装说明.md)。

克隆包含 Git LFS 文件的仓库后，需要执行：

```powershell
git lfs install
git lfs pull
```

随后分别按照 `backend/requirements.txt` 和 `frontend/package-lock.json` 安装依赖。`.venv`、`node_modules`、构建缓存和真实密钥不会进入仓库。

## 数据与合规说明

- 国际传播案例保留来源索引、证据限制和审批状态。
- 研究结果用于当前样本的描述性分析，不直接表述为国家总体偏好或因果结论。
- 请勿提交 `.env`、数据库口令、Neo4j密码或第三方服务密钥。
- 音视频素材用于项目演示时，应继续核验授权范围和比赛提交要求。

## GitHub 上传

本项目体积较大，必须按批次提交和推送。具体步骤见 [GitHub分批上传方案](docs/github-upload/UPLOAD_PLAN.md)。
