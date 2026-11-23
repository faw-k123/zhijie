# v1.5 发布前快照回滚说明

- 当前 active_version：v1.2
- 本快照保存 v1.2、v1.5、v1.5-draft 和主 manifest。
- 若未来激活 v1.5 后需要回滚：
  1. 将主 manifest 的 active_version 改回 v1.2；
  2. 使用 snapshot/v1.2 覆盖 data/v1.2（仅在确认后）；
  3. 使用 snapshot/manifest.json 恢复登记；
  4. 重新运行 validate_research_data；
  5. 验证 API 返回 36 案例。
- 本快照只读保存，不覆盖历史版本。
