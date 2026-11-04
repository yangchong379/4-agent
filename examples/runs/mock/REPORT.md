# 实际生成及检查报告

模式offline_mock，12/12场景通过。

Mock仅证明流程；真实模型可能首稿即达标，不能假称一定发生超时修正。每组目录有输入、素材、实际分镜及完整Trace。

| 场景 | 实际状态 | 秒数 | 版本 | 检查 | 输出及Trace |
|---|---|---|---|---|---|
| normal | completed | 36.5 | 1 | PASS | [result](normal/result.json) |
| duration_revision | completed | 27.5 | 2 | PASS | [result](duration_revision/result.json) |
| short_target | completed | 5 | 2 | PASS | [result](short_target/result.json) |
| missing | needs_info | None | 0 | PASS | [result](missing/result.json) |
| missing_duration | needs_info | None | 0 | PASS | [result](missing_duration/result.json) |
| no_materials | needs_materials | None | 0 | PASS | [result](no_materials/result.json) |
| rewrite | completed | 27.5 | 2 | PASS | [result](rewrite/result.json) |
| tool_retry | completed | 27.5 | 2 | PASS | [result](tool_retry/result.json) |
| tool_failure | tool_failed | None | 1 | PASS | [result](tool_failure/result.json) |
| impossible | constraints_unmet | 2 | 2 | PASS | [result](impossible/result.json) |
| replaced | completed | 27.5 | 2 | PASS | [result](replaced/result.json) |
| step_limit | incomplete_step_limit | None | 1 | PASS | [result](step_limit/result.json) |
