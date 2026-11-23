# 六国翻译 JSON 使用说明

> 协议：`IRP-SIX-COUNTRY-2026-V1` / `frozen`  
> 协议 SHA-256：`450d0352fdd9bce909a4671b6f5dc420d9620e8a5615f844c0553ebc22aff4ca`  
> 当前翻译状态：0/6  
> 当前母语审校状态：0/6

## 1. 模板在哪里

### 工作台下载

```text
http://localhost:5175/research/pilot?designPreview=1
```

进入“六国本地化与母语审校”，每个国家有：

```text
下载模板
```

### 直接文件

```text
research/candidates/v1.7-six-country-pilot/translation_templates/
```

六国模板：

```text
ja-LOC-IRP-SIX-COUNTRY-2026-V1-ja-V1.json
th-LOC-IRP-SIX-COUNTRY-2026-V1-th-V1.json
en-GB-LOC-IRP-SIX-COUNTRY-2026-V1-en-V1.json
en-US-LOC-IRP-SIX-COUNTRY-2026-V1-en-V1.json
ar-LOC-IRP-SIX-COUNTRY-2026-V1-ar-V1.json
pt-BR-LOC-IRP-SIX-COUNTRY-2026-V1-pt-BR-V1.json
```

打包文件：

```text
docs/six-country-translation-templates.zip
```

## 2. 找谁翻译

优先顺序：

1. **目标语言母语专业译者**；
2. 高校翻译系/语言系、孔子学院或当地文化机构推荐的译者；
3. 有学术问卷翻译经验的本地研究助理；
4. 目标国家的社区文化组织，但必须有独立审校。

不要：

- 只用机器翻译后直接提交；
- 让同一个人既翻译又做母语审校；
- 找不懂研究语境的普通语言校对替代母语审校；
- 让译者根据国籍推断宗教或文化偏好；
- 让译者添加原文没有的“国家性格”表述。

### 建议配置

每个国家至少：

```text
1 名母语译者
1 名不同身份的母语审校者
```

阿联酋建议增加一名熟悉宗教、服饰、影像和公共活动规范的文化顾问。

## 3. 只填写哪里

只填写：

```json
"translations": { ... }
```

不要修改：

```text
protocol_version
protocol_sha256
country
language
localization_version
source_zh
```

字段必须全部填写：

```text
title
intro
background_100
consent
questionnaire（7 项，每项 prompt/anchor_1/anchor_5）
open_questions（3 项）
risk_notice
recruitment
operator_manual（5 项）
```

`questionnaire` 的 `id` 必须保持：

```text
emotional_resonance
timbre_identity
melody_accessibility
cultural_story
adaptation_space
visual_expressiveness
era_theme_relevance
```

## 4. 翻译要求

- 保留 1—5 量表结构；
- 1 分和 5 分锚点要能区分；
- 不添加研究假设、排名或“国家偏好”；
- 不改变题目含义；
- 文化风险提示要保留；
- 同意文本必须完整；
- 100 字以内曲目背景不能扩写成宣传文案；
- 对“宗教、服饰、舞蹈、娱乐场景”做本地合规审查；
- 日本、泰国等地区也不能假定“天然理解中国文化”。

## 5. 提交与审校

### 翻译者提交

由项目 `operator` 身份在工作台上传填写后的 JSON：

```text
导入翻译JSON
```

提交后：

```text
status = pending_native_review
translator = 服务端 operator 身份
```

### 母语审校

由另一名 `approver` 身份审批：

```text
审批审校
```

审批后：

```text
status = approved
reviewer = 服务端 approver 身份
```

同一个身份不能同时是翻译者和审校者。

### 令牌

服务端签发：

```bash
python manage.py issue_pilot_token <translator-operator> operator
python manage.py issue_pilot_token <native-reviewer> approver
```

不要把 `approver` 令牌交给翻译者。

## 6. 六国完成标准

```text
6/6 status = approved
recruitment_ready = true
```

在此之前：

```text
正式招募 = CLOSED
```

## 7. 常见错误

| 错误 | 结果 |
|---|---|
| 修改协议 SHA | 拒绝导入 |
| 缺少题目/锚点 | 拒绝导入 |
| 只填一部分国家 | `recruitment_ready=false` |
| 同一人翻译并审批 | 拒绝审批 |
| 机器翻译直接审批 | 不允许；必须母语审校 |
| 用中文母版直接测试 | 不允许正式招募 |

## 8. 当前下一步

把 `docs/six-country-translation-templates.zip` 发给六国母语译者。  
每国回收一份填写后的 JSON，再由独立母语审校者审批。  
当前没有真实翻译，不能把 `source_ready` 写成 `approved`。
