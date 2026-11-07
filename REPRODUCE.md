# 重跑 ORA 实验

只想核对历史结果？在本仓库执行 `python3 scripts/verify.py`。重跑仿真才需要下面的 GPU 环境。

## 1. 准备固定版本与服务

固定 ORA 提交 `4d7a26f7c52a18a9f1af292e967aa8b7a526ac61`，按该版本的 [单 GPU 配置](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/docs/getting-started/single-gpu.md)、[LIBERO 安装](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/docs/environments/libero.md) 和 [感知服务配置](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/docs/environments/common.md#install-the-shared-perception-services) 准备锁定环境、EGL、cuRobo、SAM3 与 Contact-GraspNet。记录的后端、任务数据和规划器版本见 [归档运行配置](evidence/random/20261107/recorded-spec.json)。

以下命令都在 **ORA 上游 checkout** 执行；让 `REPRO_DIR` 指向本仓库的绝对路径。按上游说明配置一张可用 GPU（多卡机器要选对宿主配置、物理 GPU 和 EGL 设备）。

## 2. DeepSeek：一个场景、一个回合

通过环境变量 `DEEPSEEK_LOW_API_KEY` 配置自己的官方 API 凭据，然后运行：

```bash
./scripts/ora run --env libero --task libero_goal/0 --seed 0 \
  --provider-profile deepseek_flash_openai_low_16k_v1 --confirm-launch
```

预检和运行会产生 API 用量。本次响应模型标识是 `deepseek-flash`；服务别名会更新，复跑不保证命中原服务端版本或得到相同轨迹。以新 run 的原生 `result.json` 和 `evaluation.json` 为准。

## 3. 随机对照：无需模型 API

用上游 `./scripts/model-services qualify` 取得当前感知服务的 readiness JSON 路径；随机策略不使用感知结果，但绑定与成功回合同类的工具栈。重建配置时使用当前服务绑定，而不是归档的进程信息。

```bash
unset DEEPSEEK_LOW_API_KEY DEEPSEEK_API_KEY
uv run --locked python "$REPRO_DIR/scripts/prepare_random.py" \
  --readiness "$READINESS_JSON" --experiment ora-random-recheck --dest "$PWD/random-recheck-specs"
./scripts/ora plan random-recheck-specs/random-20261107.json
./scripts/ora launch random-recheck-specs/random-20261107.json
```

使用多卡自定义配置时，给生成器传入本机的 `--host` 和 `--resource-profile`。用 `./scripts/ora status RUN_ID` 查看状态，待该回合结束并释放 slot 后再运行其余两个种子。每个种子先生成 200 个提议，运行以 80 个计入预算的决策（或更早的环境终止/其他预算）为界；不要按提议数截成 80。原始三组序列与重建序列可通过离线脚本核对。

重建启动辅助未另行运行新的仿真回合。历史结果来自原生 ORA 入口，三组固定随机提议未改动。
