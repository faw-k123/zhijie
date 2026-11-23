# v1.6 发布前快照回滚说明

- 快照时 active_version：v1.5
- 保存 v1.5 完整数据、主 manifest、active_version.txt。
- 若 v1.6 激活后需要回滚：
  1. 将主 manifest 的 active_version 改回 v1.5；
  2. 使用 snapshot/v1.5 核对；
  3. 重新运行 validate_research_data；
  4. 验证 API 回到 38 案例；
  5. 不删除 v1.6，保留审计。
- 本快照只读保存，不覆盖历史版本。
