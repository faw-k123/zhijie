# P17-E 第二批前端展示修正清单

## 1. 修改范围

仅修改前端展示文字、状态标签和样式，不修改正式数据、API、评分算法。

### 案例库

- `SampleBadge` 增加 `mode="library"`；
- 案例库徽章改为：

```text
案例库收录 40/40
```

- 辅助文字改为：

```text
案例库收录量，不代表严格样本规模
```

### 案例详情

新增样本状态提示条：

```text
严格个人样本（已批准）
扩展跨文化样本
待核实 · 不纳入严格个人样本
审批：已批准 / 待补证 / 无需审批
已评分 N 项 · 未知 N 项
```

评分区标题改为：

```text
已评分指标均值（仅供描述）
```

说明改为：

```text
均值仅描述已评分指标，不代表证据等级、传播成功率或排名。
```

相似案例中的“编码均分”改为：

```text
已评分均值
```

### 案例列表/预览

- `CaseLibraryRow`：`编码均分` → `已评分均值`；
- `CasePreviewCard`：`编码均分` → `已评分均值`。

## 2. CASE007 显示

浏览器实测：

```text
待核实 · 不纳入严格个人样本
审批：待补证
7 项有效
```

未把未知项显示为 0，未将 2.71/3 描述为传播效果。

## 3. CASE039/040 显示

```text
扩展跨文化样本
审批：已批准
9 项有效 / 1 未知
6 项有效 / 4 未知
```

## 4. 验证

```text
npm run type-check：passed
npm run build-only：passed
```

浏览器实测：

- 案例库显示“案例库收录 40/40”；
- 旧“描述性样本 · 40/40”不再出现；
- CASE007 待核实标签出现；
- CASE039/040 审批与样本标签正常。

## 5. 数据安全

```text
active_version = v1.6
v1.6 数据未修改
API 未修改
评分算法未修改
```

## 6. 修改文件

- `frontend/src/components/research/SampleBadge.vue`
- `frontend/src/components/research/CaseLibraryRow.vue`
- `frontend/src/components/research/CasePreviewCard.vue`
- `frontend/src/views/GlobalCaseLibraryView.vue`
- `frontend/src/views/GlobalCaseDetailView.vue`
