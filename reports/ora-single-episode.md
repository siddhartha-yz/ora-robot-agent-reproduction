# ORA 单任务复现：成功打开中层抽屉

2026-11-07，在课题组服务器上运行 **1 个任务、1 个回合**。LIBERO 官方判定 `official_success=true`，ORA 评估为 `valid`，`behavioral_sample_valid=true`。

## 看结果

- **录像：**`打开中层抽屉.mp4`，25 秒、1920×960、双相机原始仿真画面；去掉了等待模型推理的时间，未重新运行模拟器。
- **实际耗时：**388.740 秒（6 分 29 秒）。
- **执行量：**16 次模型调用、7 次机器人动作、498 个环境步。
- **API 用量折算：**回合 ¥0.363293，4 次预检 ¥0.002071，合计约 **¥0.37**。这是响应 usage 按闲时公开价计算的估算，非账户账单；输出 token 已包含推理，不重复计费。

## 实际发生了什么

模型用 SAM3 定位把手、查询深度坐标。Contact-GraspNet 未给出可用抓取候选，模型随后自行计算预抓取位置和夹爪朝向；靠近后用腕相机重新定位，微调、夹紧，再分三次拉出抽屉。最后 `check_task` 返回成功。

末次动作的位置残差约 3.63 cm，超出该动作 1.5 cm 的到位容差，但抽屉开度已满足 LIBERO 的官方条件。成功依据是环境终止信号，不是模型的结束语。

## 复现配置

- 任务：`libero_goal/0`，`open the middle drawer of the cabinet`，seed `0`。
- 模型：DeepSeek 官方 API `https://api.deepseek.com`，API 返回标识 `deepseek-flash`，`reasoning_effort=low`，输出上限 16,384。
- 响应 `system_fingerprint`：`bc19ba97cbe016479903222bb1578db6`。接口仅返回别名，未据此推断独立权重快照。
- ORA：`4d7a26f7c52a18a9f1af292e967aa8b7a526ac61`，源码、提示词与任务检查器均未修改。
- LIBERO-PRO：`2b910b5b5f53016bef9907632f6f840f1ce2229c`；任务数据：`c86fc3b8293185a6f373677018ff3e37f8391602`。
- 完整 GPU 工具配置：SAM3、Contact-GraspNet、cuRobo；单张 RTX 4090。未使用本机 GPU，也未人工指导本回合动作。

## 文件与继续使用

- [原始捕获录像](../media/open-middle-drawer.mp4) · [完成画面](../media/open-middle-drawer-final.png)
- [原生结果](../evidence/deepseek/result.json) · [评估记录](../evidence/deepseek/evaluation.json) · [用量与费用](../evidence/deepseek/cost.json)
- [逐轮模型输出与实际执行的对照](model-role.md) · [复现步骤](../REPRODUCE.md)

来源：[ORA 对应源码](https://github.com/hao-ai-lab/ORA/tree/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61)、[DeepSeek 价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)。
