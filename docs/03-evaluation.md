# 03 预期、实际结果及限制

Python 3.11.4实际执行：25个自动化测试通过，12/12离线场景通过。[原始报告](../examples/runs/mock/REPORT.md)、[summary](../examples/runs/mock/summary.json)、[测试日志](../examples/runs/mock/tests.txt)。不是人工编写成功截图，分镜与检查原始记录均在examples。

| 场景 | 预期 | 实际 | 秒数 | 版本 | 证据 |
|---|---|---|---|---|---|
| normal | completed | completed | 36.5 | 1 | [input](../examples/runs/mock/normal/input.json) · [result](../examples/runs/mock/normal/result.json) |
| duration_revision | completed | completed | 27.5 | 2 | [input](../examples/runs/mock/duration_revision/input.json) · [result](../examples/runs/mock/duration_revision/result.json) |
| short_target | completed | completed | 5 | 2 | [input](../examples/runs/mock/short_target/input.json) · [result](../examples/runs/mock/short_target/result.json) |
| missing | needs_info | needs_info | None | 0 | [input](../examples/runs/mock/missing/input.json) · [result](../examples/runs/mock/missing/result.json) |
| missing_duration | needs_info | needs_info | None | 0 | [input](../examples/runs/mock/missing_duration/input.json) · [result](../examples/runs/mock/missing_duration/result.json) |
| no_materials | needs_materials | needs_materials | None | 0 | [input](../examples/runs/mock/no_materials/input.json) · [result](../examples/runs/mock/no_materials/result.json) |
| rewrite | completed | completed | 27.5 | 2 | [input](../examples/runs/mock/rewrite/input.json) · [result](../examples/runs/mock/rewrite/result.json) |
| tool_retry | completed | completed | 27.5 | 2 | [input](../examples/runs/mock/tool_retry/input.json) · [result](../examples/runs/mock/tool_retry/result.json) |
| tool_failure | tool_failed | tool_failed | None | 1 | [input](../examples/runs/mock/tool_failure/input.json) · [result](../examples/runs/mock/tool_failure/result.json) |
| impossible | constraints_unmet | constraints_unmet | 2 | 2 | [input](../examples/runs/mock/impossible/input.json) · [result](../examples/runs/mock/impossible/result.json) |
| replaced | completed | completed | 27.5 | 2 | [input](../examples/runs/mock/replaced/input.json) · [result](../examples/runs/mock/replaced/result.json) |
| step_limit | incomplete_step_limit | incomplete_step_limit | None | 1 | [input](../examples/runs/mock/step_limit/input.json) · [result](../examples/runs/mock/step_limit/result.json) |

duration_revision中首稿36.5秒，目标30秒，estimate_duration返回超6.5秒；下一步完成规则核对，随后重新compose压缩停留，得到27.5秒，再估时与核规则均通过，finish才completed。impossible目标1秒，修订后单镜最低2秒，仍失败，最终constraints_unmet；未把2秒说成1秒。

校验包括逐镜求和、同版本双检查、素材原文/ID一致、修改使旧检查失效、编造80%与错引P02被拒、全中性稿不算事实脚本、一次失败后恢复、持续失败与有限步数。HTTP伪响应测试只验证回传观察/调用ID和脱敏，不能当作真实模型效果。

本轮真实模型已执行（详见新增实际记录）。即使真实正常用例首稿直接在时长内，也只能据实际Trace报告，不伪造“先超时后修正”；无论是修订还是明确失败，都须有真实检查记录。后续live记录独立目录保留。

已知限制：4字/秒是确定性模拟，不代表不同语言、口播、音乐或实际成片；标题/分镜/旁白候选范围有限，只能证明受限生成的可追溯性。无开放语义事实校验、平台完整规则、实际效果数据、视频渲染或生产发布；素材事实自身真实性仍需上游资料审核。用户自由编辑后旧检查失效，必须重新提交。

## 2026-11-05真实运行

真实模型自动断言12/12通过；业务复核另发现1例不满足原主题；耗时824.828秒。[原始报告](../examples/runs/live-20261105-014727-396675/REPORT.md)、[Trace复核](../examples/runs/live-20261105-014727-396675/REVIEW.md)、[文件及事实核查](../examples/runs/live-20261105-014727-396675/review.json)。原始失败保留，不宣称单次通过率能代表生产可靠性。
