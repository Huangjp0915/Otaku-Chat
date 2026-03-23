# 突破次元壁 / Otaku Chat

<p align="center">
  <strong>一个本地运行的、伪微信风格的二次元角色即时通讯桌面应用</strong>
</p>

<p align="center">
  让用户感觉自己不是在“调用一个 AI 接口”，而是真的在和角色本人聊天、加好友、看动态、推进关系。
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688" />
  <img alt="pywebview" src="https://img.shields.io/badge/pywebview-Desktop-4B5563" />
  <img alt="Frontend" src="https://img.shields.io/badge/HTML%20%2F%20CSS%20%2F%20JS-Static_UI-orange" />
  <img alt="LLM" src="https://img.shields.io/badge/LLM-mock%20%7C%20Ollama-7C3AED" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## 目录

- [项目简介](#项目简介)
- [核心目标](#核心目标)
- [当前功能一览](#当前功能一览)
- [技术架构](#技术架构)
- [界面结构](#界面结构)
- [运行模式](#运行模式)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [项目目录结构](#项目目录结构)
- [角色系统设计](#角色系统设计)
- [如何新增一个角色](#如何新增一个角色)
- [数据持久化说明](#数据持久化说明)
- [主要 API 一览](#主要-api-一览)
- [桌面打包](#桌面打包)
- [训练与 LoRA 目录说明](#训练与-lora-目录说明)
- [开发建议](#开发建议)
- [已知问题与排查](#已知问题与排查)
- [Roadmap](#roadmap)
- [许可协议](#许可协议)

---

## 项目简介

**突破次元壁 / Otaku Chat** 是一个运行在本地的桌面聊天软件，目标不是做一个“泛用型 AI 助手”，而是做一个更接近 **微信 / LINE / QQ 风格** 的二次元角色社交应用。

在这个项目里，用户的核心体验不是“提问-回答”，而是：

- 先搜索角色并发送好友申请
- 角色不会秒回、也不会一律通过
- 通过后进入真实感更强的聊天关系
- 角色会有主动消息、节日反应、朋友圈动态
- 角色会记住用户、记住最近聊过的话题
- 关系推进后，角色语气、行为和关注点会变化

这个项目目前采用：

- **FastAPI** 作为本地后端服务
- **HTML / CSS / JavaScript** 作为本地静态前端
- **pywebview** 作为桌面壳
- **本地 JSON 文件** 作为持久化存储
- **mock / Ollama** 双模式作为对话推理入口

当前代码快照中的应用版本号为：**4.1.0**。

---

## 核心目标

这个项目的目标从来不是“把一个聊天页面做出来”，而是把它逐步打磨成一个有真实社交感的角色应用。

### 想实现的不是

- 一个只有输入框和回复框的网页 Demo
- 一个统一人格的 AI 套壳应用
- 一个只靠 prompt 临时扮演角色的聊天机器人

### 想实现的是

- 有聊天列表、通讯录、朋友圈、设置页的桌面端软件
- 有好友申请、延迟审核、通过 / 忽略 / 拒绝状态的联系人系统
- 有主动消息、纪念日、关系阶段和长期记忆的角色行为系统
- 有角色世界观、人物关系、禁忌表达、语气边界的角色设定系统
- 有“像软件产品”而不是“像实验脚本”的完整体验

一句话概括：

> **这是一个面向角色沉浸感、关系推进感和即时通讯真实感的本地桌面项目。**

---

## 当前功能一览

以下内容基于当前代码快照整理。

### 已完成的核心功能

#### 1. 本地桌面运行形态

- 后端本地启动 FastAPI 服务
- 桌面端通过 `pywebview` 打开本地页面
- 可直接作为 Windows 本地应用运行

#### 2. 四大主页面结构

当前前端已经完整具备以下页签：

- 聊天
- 通讯录
- 朋友圈
- 设置

#### 3. 联系人与“新的朋友”系统

- 初始不是全部自动成为好友
- 需要先搜索角色并发起好友申请
- 好友申请具有延迟审核逻辑
- 支持状态：等待验证 / 已通过 / 已忽略 / 已拒绝
- “新的朋友”页面已经是真实页面，而不是占位页
- 通过后可以直接发消息或重新申请

#### 4. 聊天系统

- 角色列表
- 会话详情
- 未读数
- 置顶联系人
- 删除联系人
- 聊天记录本地保存
- 不同角色按不同设定回复
- 支持延迟阅读、延迟输入、延迟发送

#### 5. 朋友圈 / 动态系统

- 主朋友圈 feed
- 角色个人朋友圈 feed
- 点赞
- 评论
- 自动生成动态
- 节日 / 关系阶段驱动的动态生成逻辑入口

#### 6. 主动消息系统

- 角色会在后台轮询中主动来找用户
- 支持多种主动触发类型
- 不是单纯随机句库，而是和最近互动相关

#### 7. 记忆与关系推进

当前代码中已经存在一版三层记忆结构：

- 短期对话上下文
- 中期关系记忆
- 长期用户印象

并且会被拼接进角色 prompt，用于影响回复。

#### 8. 特殊日期与纪念日

当前后端已具备：

- 新年
- 情人节
- 圣诞节
- 用户生日
- 加好友满 7 天
- 加好友满 30 天
- 角色纪念日

前端当前快照中也包含生日设置与节日预览入口。

#### 9. 多角色竞争事件（基础版）

当前代码中已经包含：

- 多角色同时来消息时的竞争事件创建
- 用户先回复谁的基础结算逻辑
- 未被优先回复角色的后续反应逻辑入口

#### 10. 头像系统

- 用户头像上传 / 重置
- 角色头像上传 / 重置
- 本地覆盖保存
- 静态默认头像加载

#### 11. 模型切换与设置

- `mock` 模式
- `ollama` 模式
- Ollama 模型列表读取
- 发送快捷键切换
- 主动消息轮询频率设置

---

## 技术架构

### 总体结构

```text
用户
  ↓
桌面窗口（pywebview）
  ↓
本地 FastAPI 服务
  ├─ 角色系统
  ├─ 聊天系统
  ├─ 动态系统
  ├─ 主动消息调度
  ├─ 特殊日期 / 纪念日
  ├─ 头像与运行时配置
  └─ mock / Ollama 推理入口
  ↓
本地 JSON 持久化
```

### 技术选型

#### 后端

- **FastAPI**：本地 API 服务
- **Pydantic v2**：数据结构与校验
- **Requests**：连接本地 Ollama

#### 前端

- **HTML / CSS / JavaScript**
- 不依赖大型前端框架
- 以静态资源方式由 FastAPI 挂载

#### 桌面端

- **pywebview**：将本地 Web UI 包装成桌面应用

#### 数据层

- **JSON 文件持久化**
- 适合当前单机、单用户、快速迭代阶段

#### 模型层

- **mock 模式**：无模型也可演示
- **Ollama 模式**：接本地大模型

---

## 界面结构

当前应用的界面结构如下：

### 左侧竖栏

- 聊天
- 通讯录
- 朋友圈
- 设置

### 左中列

根据当前页签切换显示：

- 聊天列表
- 通讯录列表
- 设置导航快捷入口

### 中间主区域

根据当前页签显示：

- 聊天内容区
- 设置页内容
- 朋友圈主内容
- 通讯录主页面

### 右侧抽屉 / 面板

- 角色资料
- 事件回顾
- 添加联系人抽屉
- 上下文菜单（置顶 / 删除）

这套结构的设计目标，是让用户明显感觉自己在用“一个社交应用”，而不是在用“一个 prompt playground”。

---

## 运行模式

### 1. mock 模式

适合以下场景：

- 首次启动项目
- 不想先安装本地模型
- 先验证 UI、角色系统和流程
- 做前端和交互调试

优点：

- 零门槛
- 启动快
- 方便调试

### 2. Ollama 模式

适合以下场景：

- 你已经有本地模型环境
- 想让角色回复更自然
- 想进一步测试角色 prompt 和记忆系统

当前默认配置示例：

- Ollama Base URL: `http://127.0.0.1:11434`
- 默认模型：`qwen3:8b`

---

## 快速开始

以下步骤面向 Windows 本地开发环境。

### 环境要求

推荐：

- **Python 3.12**
- Windows 10 / 11
- 已安装 Git（可选）

不建议优先使用：

- Python 3.13 free-threaded 版本

### 1. 克隆或解压项目

```bash
git clone <your-repo-url>
cd "Otaku Chat"
```

### 2. 进入 backend 目录并创建虚拟环境

```bash
cd backend
python -m venv .venv
```

### 3. 激活虚拟环境

#### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

#### CMD

```cmd
.venv\Scripts\activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

当前依赖包括：

- fastapi
- uvicorn[standard]
- pydantic
- pydantic-settings
- python-dotenv
- requests
- pywebview
- python-multipart

### 5. 启动方式一：桌面端

```bash
python run_desktop.py
```

这会：

- 启动本地 FastAPI 服务
- 等待服务就绪
- 打开桌面窗口

### 6. 启动方式二：浏览器调试模式

```bash
python run_server.py
```

这会：

- 启动本地 FastAPI 服务
- 自动在浏览器打开页面

适合：

- 调试前端样式
- 看 console 日志
- 快速前后端联调

---

## 配置说明

### `.env` 文件位置

项目读取的是：

```text
backend/.env
```

### 常用配置项

```env
APP_HOST=127.0.0.1
APP_PORT=8000
LLM_MODE=mock
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
USER_ID=default_user
DESKTOP_WINDOW_TITLE=突破次元壁
PROACTIVE_COOLDOWN_SECONDS=120
```

### 配置项说明

| 配置项 | 说明 |
|---|---|
| `APP_HOST` | 本地服务监听地址 |
| `APP_PORT` | 本地服务端口 |
| `LLM_MODE` | `mock` 或 `ollama` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 |
| `OLLAMA_MODEL` | 默认使用的 Ollama 模型 |
| `USER_ID` | 当前用户唯一 ID |
| `DESKTOP_WINDOW_TITLE` | 桌面窗口标题 |
| `PROACTIVE_COOLDOWN_SECONDS` | 主动消息冷却时间 |

---

## 项目目录结构

```text
Otaku Chat/
├─ LICENSE
├─ README.md
└─ backend/
   ├─ requirements.txt
   ├─ run_desktop.py              # 桌面模式入口
   ├─ run_server.py               # 浏览器调试入口
   ├─ otaku_chat.spec             # 打包配置
   ├─ app/
   │  ├─ config.py                # 全局配置与目录定义
   │  ├─ main.py                  # FastAPI 入口与 API 注册
   │  ├─ schemas.py               # Pydantic 数据结构
   │  ├─ data/
   │  │  ├─ characters/           # 角色配置 JSON
   │  │  ├─ conversations/        # 聊天存档
   │  │  └─ runtime/              # 运行时数据
   │  │     ├─ avatar_overrides.json
   │  │     ├─ moments.json
   │  │     ├─ pending_friend_requests.json
   │  │     ├─ pending_jobs.json
   │  │     ├─ runtime_settings.json
   │  │     ├─ user_profile.json
   │  │     └─ uploads/
   │  ├─ services/
   │  │  ├─ avatar_service.py
   │  │  ├─ character_service.py
   │  │  ├─ chat_service.py
   │  │  ├─ llm_service.py
   │  │  ├─ memory_service.py
   │  │  ├─ moment_service.py
   │  │  ├─ prompt_service.py
   │  │  ├─ runtime_service.py
   │  │  ├─ simulation_service.py
   │  │  └─ special_date_service.py
   │  └─ static/
   │     ├─ index.html            # 前端结构
   │     ├─ style.css             # 前端样式
   │     ├─ app.js                # 前端逻辑
   │     └─ assets/
   │        └─ avatars/           # 默认角色头像
   └─ train/
      ├─ README_TRAINING.md
      ├─ export_chat_for_training.py
      ├─ sample_roleplay_dataset.jsonl
      └─ train_lora_unsloth.py
```

---

## 角色系统设计

这是本项目最核心的部分之一。

### 角色不是一段 prompt，而是一张完整角色卡

每个角色都以一个 JSON 文件存在，文件中通常会包含：

- 基础信息：`id` / `name` / `avatar` / `title` / `source`
- 性格描述：`personality` / `speech_style` / `speech_habits`
- 世界观与关系：`world_knowledge` / `canon_relationships`
- 设定边界：`taboo` / `canon_guardrails`
- 对话启动：`greetings` / `starter_topics` / `proactive_lines`
- 行为参数：`friend_behavior` / `reply_behavior` / `proactive_behavior`
- 节日与动态：`anniversary_dates` / `festival_lines` / `moment_topics`
- 状态文本：`status_texts`

### 角色系统的目标

不是单纯“模仿一个说话风格”，而是确保：

- 人设不乱
- 世界观不串
- 人物关系不乱
- 角色不会突然变成客服
- 关系推进后表现会变化

### 当前角色加载方式

角色由后端自动扫描：

```text
backend/app/data/characters/*.json
```

这意味着：

- 不需要手动注册角色到某个列表
- 不需要改前端路由
- 只要 JSON 合法，角色就会自动出现在系统里

---

## 如何新增一个角色

### 1. 新建角色 JSON

放到：

```text
backend/app/data/characters/
```

例如：

```text
backend/app/data/characters/04_asuna_yuuki.json
```

### 2. 放入角色头像

放到：

```text
backend/app/static/assets/avatars/
```

### 3. 头像字段必须写成可访问 URL

正确写法：

```json
"avatar": "/static/assets/avatars/asuna.jpg"
```

不要写成：

```json
"avatar": "backend/app/static/assets/avatars/asuna.jpg"
```

因为前端需要的是 URL，不是磁盘路径。

### 4. 重启程序

新增角色后需要重启后端或桌面应用，角色才会刷新出来。

### 5. 角色设计建议

建议每个角色至少写清楚这些内容：

- 作品来源与世界观边界
- 重要人物关系
- 禁忌表达
- 说话方式
- 熟悉前 / 熟悉后 / 亲近后差异
- 节日与主动消息语气

如果这些不清楚，大模型很容易：

- 串作品设定
- 串人物关系
- 一聊久就崩人设

---

## 数据持久化说明

当前项目主要使用本地 JSON 存储。

### 角色数据

```text
backend/app/data/characters/
```

### 聊天记录

```text
backend/app/data/conversations/
```

### 运行时数据

```text
backend/app/data/runtime/
```

其中包括：

- `runtime_settings.json`：模型、快捷键、轮询间隔等
- `pending_friend_requests.json`：待审核好友申请
- `pending_jobs.json`：延迟回复任务
- `moments.json`：朋友圈内容
- `avatar_overrides.json`：头像覆盖记录
- `user_profile.json`：用户生日等资料
- `uploads/`：用户上传头像文件

### 优点

- 开发简单
- 可直接查看和调试
- 适合单机原型

### 局限

- 不适合多用户并发
- 不适合复杂查询
- 不适合作为长期线上数据库方案

对于当前阶段，这种设计是合理的，因为重点是快速迭代体验，不是先上数据库中台。

---

## 主要 API 一览

下面是当前快照中的主要接口分类。

### 运行时 / 设置

- `GET /api/runtime/status`
- `POST /api/runtime/update`

### 角色与联系人

- `GET /api/characters`
- `GET /api/characters/{character_id}`
- `POST /api/contacts/{character_id}/add`
- `POST /api/contacts/{character_id}/delete`
- `POST /api/contacts/{character_id}/pin`
- `GET /api/friends/requests`

### 会话与聊天

- `GET /api/conversations/{character_id}`
- `POST /api/conversations/{character_id}/increment-unread`
- `POST /api/chat`
- `POST /api/conversations/{character_id}/reset`
- `GET /api/proactive/check-all`

### 朋友圈 / 动态

- `GET /api/moments/feed`
- `GET /api/moments/character/{character_id}`
- `POST /api/moments/{moment_id}/like`
- `POST /api/moments/{moment_id}/comment`

### 头像管理

- `POST /api/avatar/upload/{character_id}`
- `POST /api/avatar/reset/{character_id}`
- `POST /api/avatar/upload-user`
- `POST /api/avatar/reset-user`

### 用户资料 / 节日

- `GET /api/user/profile`
- `POST /api/user/profile`
- `GET /api/special-dates/preview`

---

## 桌面打包

项目当前已经包含：

```text
backend/otaku_chat.spec
```

说明已经为 Windows 打包预留了 PyInstaller 配置方向。

一个常见打包流程通常会是：

```bash
pip install pyinstaller
pyinstaller otaku_chat.spec
```

打包前建议先确认：

- 本地运行稳定
- 静态资源路径正常
- 默认头像路径为 `/static/...`
- 当前虚拟环境干净
- 未把无关缓存文件一并打包

### 打包前建议检查

- 是否误把 `.venv` 提交进仓库
- 是否误把临时上传头像带进发布包
- 是否误把调试日志和测试数据带进发布包

---

## 训练与 LoRA 目录说明

项目中已经预留了训练目录：

```text
backend/train/
```

其中包括：

- `sample_roleplay_dataset.jsonl`：样例数据集
- `export_chat_for_training.py`：导出聊天记录的基础脚本
- `train_lora_unsloth.py`：LoRA 微调模板
- `README_TRAINING.md`：训练说明

### 当前建议

训练不是第一优先级。

更推荐的顺序是：

1. 先把软件跑起来
2. 先把角色系统写稳
3. 先把多角色聊天体验调顺
4. 再整理高质量样例对话
5. 最后再考虑 LoRA 微调

### 原因

角色像不像，不只取决于模型是否微调，还取决于：

- 角色卡写得是否清楚
- 世界观边界是否稳
- 记忆系统是否有效
- 主动消息逻辑是否自然
- 关系推进是否合理

因此，不建议过早把所有问题都寄希望于微调。

---

## 开发建议

### 1. 把项目当桌面软件做

不要把它当成一个公网 Web 产品去设计第一阶段架构。

当前最合理的路线是：

- 本地 API
- 本地静态前端
- pywebview 桌面壳
- 单机 JSON 持久化

### 2. 优先把“角色像人”做出来

优先级高于：

- 炫技模型
- 复杂数据库
- 分布式系统
- 过度工程化

### 3. 新增角色时先保质量，再堆数量

角色多不代表体验好。

如果想批量扩角色，最先要稳住的是：

- `world_knowledge`
- `canon_relationships`
- `canon_guardrails`
- `taboo`
- `system_prompt`

### 4. 先做强体验，再做强平台

最打动人的不是“接了多少系统”，而是：

- 角色说话像不像
- 主动来找你有没有真实感
- 朋友圈像不像活的
- 关系推进有没有层次

---

## 已知问题与排查

### 1. 图片明明放进 `static/assets/avatars` 了，但界面显示不出来

最常见原因是角色 JSON 里写的是磁盘路径，而不是 URL。

#### 正确写法

```json
"avatar": "/static/assets/avatars/rem.png"
```

#### 错误写法

```json
"avatar": "backend/app/static/assets/avatars/rem.png"
```

### 2. 运行 `run_desktop.py` 时服务启动失败

优先检查：

- 是否有 Python import 错误
- 是否有接口或 schema 改了一半
- 端口是否被占用
- `.venv` 依赖是否完整

### 3. 新加的角色没有显示

检查：

- JSON 是否合法
- 文件是否放在 `backend/app/data/characters/`
- `id` 是否重复
- 程序是否已重启

### 4. 上传头像后能显示，但默认头像不显示

原因通常仍然是默认头像路径写错。

上传头像会存成 `/user-content/...`，这是正确 URL；默认头像要写成 `/static/...`。

### 5. Python 版本问题

推荐使用 **Python 3.12**。

如果你使用的是较新的实验性 Python 版本，可能会遇到一些依赖兼容或运行异常问题。

---

## Roadmap

下面是当前比较清晰的后续方向。

### 高优先级

- [ ] 统一项目内自定义弹窗系统，替换原生 `alert` / `confirm`
- [ ] 继续强化多角色竞争事件表现层
- [ ] 节日 / 纪念日端到端联调
- [ ] 动态评论自动回复更自然
- [ ] 角色头像路径与覆盖系统进一步稳固

### 中优先级

- [ ] 角色池扩充
- [ ] 角色专属剧情节点扩展
- [ ] 更细的关系阶段行为变化
- [ ] 更丰富的朋友圈内容生成策略
- [ ] 更完整的设置页与交互反馈

### 长期方向

- [ ] Live2D / 语音 / 表情反馈
- [ ] 更强的本地模型接入层
- [ ] 更成熟的角色训练数据导出与微调流程
- [ ] Windows 安装包与一键分发
- [ ] 更完整的产品包装与发布版体验

---

## 许可协议

本项目当前仓库中包含 `LICENSE` 文件，请以仓库根目录中的许可证文件为准。

如果你打算：

- 二次分发
- 商业使用
- 引入已有动漫角色设定或素材
- 公开发布可下载版本

请务必额外确认：

- 图片素材授权
- 角色 IP 使用边界
- 模型与数据来源授权
- 你自己的发布范围和风险控制方式

---

## 最后一段

如果你正在看这个 README，说明你拿到的不只是一个聊天页面，而是一个已经具备明确产品方向的本地桌面项目。

它当前最重要的事，不是继续“加更多技术名词”，而是把以下这几件事越做越真：

- 角色像不像本人
- 关系推进有没有层次
- 社交感够不够真实
- 软件本身像不像一个完整产品

如果这些都做出来了，这个项目就会从“一个能跑的角色聊天 Demo”，真正走向“一个有辨识度的二次元桌面社交软件”。
