# 短视频脚本 Agent · 题目4

根据合成产品素材，形成有来源、可编辑的标题、分镜、旁白和时长检查结果。独立仓库：[yangchong379/4-agent](https://github.com/yangchong379/4-agent)。Python 3.11+标准库，无Agent框架或第三方运行依赖，无真实发布。

当前实际结果：**25个自动化测试、12/12离线场景通过**。30秒目标首稿实际估算36.5秒，模型Mock策略观察超限后调整停留和分镜，修订为27.5秒，并再次估时和核规则。1秒目标修订仍为2秒，明确constraints_unmet。Mock只验证流程，尚未进行本项目真实模型验证。

```bash
python scripts/run.py --input examples/inputs/duration_revision.json --output .runtime/script.json
python -m unittest discover -s tests -v
python scripts/evaluate.py --output .runtime/recheck
```

Windows用`py -3.11`替代python；命令在本仓库根目录运行。可选`python -m pip install -e .`后用short-video-agent。每次评估必须选新目录，不覆盖已有证据。

输入示例：

```json
{"request_id":"creator-001","topic":"小影字幕","audience":"新手创作者","platform":"抖音","target_seconds":30,"style":"轻松"}
```

主题、受众、平台、目标时长和风格缺失时返回needs_info。目标是1–180整数秒，按上限校验；观感和真实成片时长没有保证。输出含title、storyboard、narration、逐镜estimated_seconds、estimated_total_seconds、source_material_ids、risks、status、当前版本两份检查和完整Trace。

评审材料：[需求](docs/01-requirements.md)、[方案](docs/02-solution.md)、[评估](docs/03-evaluation.md)、[AI记录](docs/04-ai-usage.md)、[复盘](docs/05-retrospective.md)、[实际分镜及检查](examples/runs/mock/REPORT.md)、[测试输出](examples/runs/mock/tests.txt)。

真实模型入口（本机密码弹窗输入密钥，不发到聊天）：

```powershell
py -3.11 scripts/connect_deepseek.py --evaluate
py -3.11 scripts/connect_deepseek.py --retry-failed
```

使用DeepSeek工具调用；自定义兼容接口见.env.example，不自动加载.env。每轮由真实模型选择检索、compose_script、estimate_duration、check_rules或finish，观察结果再选下一步；默认32步，可设1–100，超限/模型错误明确未完成，不回退Mock。HTTP适配器和本机窗口复用通用逻辑，项目运行独立。

事实边界：旁白每行只能是已检索素材中的逐字事实并带正确ID，或已批准中性话语；标题和画面从有限集合选择。模型可组合顺序、分镜、停留、中性开场和事实；**这是受限脚本编排，不是任意创意文案生成或语义事实核验**。P01只有“支持字幕。”时，写“效率提升80%”或借P02错误引用均无法通过。至少一条事实来源才可完成；外部自由编辑后必须重新检查。

时长按每秒4个朗读字符、每镜至少2秒加显式停留估算，不是TTS或视频实测。修改脚本即作废两份旧检查，只有同一最新版本估时与规则都通过才completed。工具失败可重试后停止，未验证稿保留但明确非完成。CLI完成退出0，明确缺口/工具失败等退出2，步数/模型错误退出3，配置输入错误退出4。

支持的小影产品素材和品牌规则全为合成，不声明真实产品能力或实际平台合规。尚无官方素材审核、自由文本蕴含检查、真实音视频生成、自动发布、内容质量盲评、生产权限或部署。
