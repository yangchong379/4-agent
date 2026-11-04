# 01 需求与成功标准

用户为创作者；输入主题、受众、平台、时长上限和风格，工具提供产品事实检索、实际时长估算、品牌规则核对。交付可编辑标题、分镜、旁白、时长、素材ID、风险和状态。

| 必验收点 | 实际输出及Trace |
|---|---|
| 正常生成 | [normal](../examples/runs/mock/normal/result.json) |
| 缺关键信息 | [missing](../examples/runs/mock/missing/result.json)、[missing_duration](../examples/runs/mock/missing_duration/result.json) |
| 无素材 | [no_materials](../examples/runs/mock/no_materials/result.json)，两种查询无结果后补资料 |
| 工具失败 | [tool_failure](../examples/runs/mock/tool_failure/result.json)，稿件保留但未验证 |
| 超时修订 | [duration_revision](../examples/runs/mock/duration_revision/result.json)，36.5→27.5秒且两项重查 |
| 无法满足 | [impossible](../examples/runs/mock/impossible/result.json)，1秒目标修订仍2秒，明确失败 |

补充验收：同义改写检索、一次工具错误恢复、短时长删减、替换素材事实、有限步数、错误ID/80%结论/未检查结束保护。每个目录保存input、dataset和真实程序输出result，Trace内有动作参数、观察和后续动作。
