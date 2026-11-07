# 这次 ORA 的任务决策在哪里

审计对象是上次成功运行实际使用的 ORA commit `4d7a26f7c52a18a9f1af292e967aa8b7a526ac61`、LIBERO `libero_placement_direct_overhead_v1` surface，不把仓库其他 surface 的能力混进来。

## 判断

没有找到根据“中层抽屉”任务名自动执行“找把手→接近→夹紧→拉开”的任务级分支。这次运行是模型逐轮给出目标和动作参数，感知与传统控制工具执行；不是模型先写出一整段可执行机器人 policy。

| 模型指定 | 代码/预训练工具执行 |
|---|---|
| 查询哪个对象、用哪台相机 | SAM3 分割、RGB-D 几何 |
| 采用哪个抓姿，或自行指定接近姿态 | Contact-GraspNet 候选、几何数值计算 |
| 目标位置、姿态、运动意图 | cuRobo / IK / 通用密集反馈控制 |
| 何时闭合、拉动方向和距离、下一步动作 | 当前位姿下执行夹爪和运动指令，并返回测量反馈 |

这些工具已经承担大量机器人能力，单个任务的随机对照不能量化各模块的贡献。

## 决定性代码

所有链接固定到本次实际运行的 commit：

- [surface 允许的变更世界工具](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/policy/tool_surfaces/explicit_motion_v3/libero_placement_direct_overhead_v1-manifest.json#L77-L116)：只有位姿、旋转、夹爪、等待等，没有 `grasp_execute`、`place_execute` 或 `open_drawer`；[dispatch 按 surface 拒绝其他工具](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/runtime/core.py#L405-L409)。
- [grounding 查询来自模型提供的 camera/text](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/runtime/perception.py#L114-L185)，不靠任务名自动选目标，也不运动。
- [抓取规划只返回候选及检查结果](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/runtime/grasp.py#L92-L151)，不自动执行接近、夹紧或拉开。
- [位姿工具读取显式数值目标后提交](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/runtime/move_pose.py#L176-L266)；[运动路由只根据位姿差和 interaction](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/environment/backends/libero_pro/sparse_motion.py#L169-L248)，不根据抽屉任务名决策。
- [夹爪命令保持当前末端位姿](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/environment/backends/libero_pro/local_motion.py#L233-L240)；[通用反馈控制器把误差变成 OSC 命令](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/environment/backends/libero_pro/local_motion.py#L284-L429)。
- `compute` 是[无文件/网络/环境访问的数值计算](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/compute.py#L1-L25)；[禁止 import、函数定义和循环等](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/compute_grammar.py#L63-L77)，[数学 namespace 没有 robot API](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/tools/compute_namespace.py#L127-L140)。
- [任务文字被送进模型上下文](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/orchestrator/context_manifest_slots.py#L59-L68)；[LIBERO 没有额外任务合同注册](https://github.com/hao-ai-lab/ORA/blob/4d7a26f7c52a18a9f1af292e967aa8b7a526ac61/ora/agent/composition/task_contract.py#L24-L72)。
