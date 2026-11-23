# v1.7 六国实测候选层

本目录只保存六国测试的候选批次和候选评分，不进入正式 `research/data/v1.7/`。

## 目录

- `batches/`：导入批次，raw / clean / rejected / errors / metadata 分层；
- `scores/`：待审批、已审批候选、已发布、已撤销的评分；
- `evidence/`：0—100 证据分及审批历史；
- `published/`：当前 active 正式发布版本；旧版本保留为 superseded；
- `config_versions/`：不可变门槛版本；
- `config_active.json`：当前生效门槛指针。
- `protocol/`：首轮试验协议候选稿、冻结版本与当前协议指针；
- `localization/<protocol_version>/`：六国中文母版、翻译稿、母语审校和摘要；
- `assignments/`：去标识化参与者分配及开始、播放、完成、提交、退出事件。

## 规则

1. 不覆盖原始批次；
2. 未同意、重复编号、缺失字段、越界数据进入拒绝层；
3. 只有已审批批次能参与聚合；
4. 只有八项完整、达到门槛且证据分已审批的单元可以有正式分；
5. 排名只能读取当前 active/published 版本；旧版本不能继续排名；
6. 导入、审批、发布、撤销均需服务端签发令牌；请求体中的姓名不作为身份；
7. 所有候选记录可追溯批次、公式、审批人与撤销记录。
8. 正式分配前，协议必须冻结，且该国家本地化材料必须由不同于翻译者的母语审校人批准；
9. 国家×曲目×原版/适配版使用最小配额优先分配，退出记录不占有效配额；
10. 本地化材料与协议 SHA-256 绑定，协议摘要变化后不得继续使用旧翻译。

## 启动

前端：`/research/pilot`

后端测试：

```bash
python manage.py test propagation.test_pilot propagation.test_protocol
```
