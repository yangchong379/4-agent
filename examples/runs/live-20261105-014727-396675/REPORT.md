# 实际生成及检查报告

模式live_model，12/12场景通过。

Mock仅证明流程；真实模型可能首稿即达标，不能假称一定发生超时修正。每组目录有输入、素材、实际分镜及完整Trace。

| 场景 | 实际状态 | 秒数 | 版本 | 检查 | 输出及Trace |
|---|---|---|---|---|---|
| normal | completed | 23.0 | 1 | PASS | [result](normal/result.json) |
| duration_revision | completed | 17.0 | 1 | PASS | [result](duration_revision/result.json) |
| short_target | completed | 4 | 1 | PASS | [result](short_target/result.json) |
| missing | needs_info | None | 0 | PASS | [result](missing/result.json) |
| missing_duration | needs_info | None | 0 | PASS | [result](missing_duration/result.json) |
| no_materials | needs_materials | None | 0 | PASS | [result](no_materials/result.json) |
| rewrite | completed | 22.0 | 1 | PASS | [result](rewrite/result.json) |
| tool_retry | completed | 11.0 | 1 | PASS | [result](tool_retry/result.json) |
| tool_failure | tool_failed | None | 1 | PASS | [result](tool_failure/result.json) |
| impossible | constraints_unmet | 2 | 2 | PASS | [result](impossible/result.json) |
| replaced | completed | 17.3 | 2 | PASS | [result](replaced/result.json) |
| step_limit | incomplete_step_limit | None | 0 | PASS | [result](step_limit/result.json) |
