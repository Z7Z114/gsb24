# 科幻小说创作头脑风暴系统

一个全栈应用，用于科幻小说创作的协作式头脑风暴。

- **思维导图**：可视化世界观设定（角色 / 物理规则 / 科技 / 社会 / 地理 / 历史 / 其他）
- **设定图库**：展示角色、场景、道具等概念图
- **音频转写**：用 Whisper 转写作者们的讨论内容
- **说话人标注**：用 pyannote 标记不同设定的负责人
- **AI 摘要**：用 OpenAI 生成包含技术原理、社会结构与时间线的 Markdown 纲要
- **邮件通知**：把纲要发给共创团队

## 项目结构

```
.
├── backend/
│   ├── main.py               # FastAPI 应用与 /token /register /users/me
│   ├── models.py             # SQLAlchemy 模型
│   ├── schemas.py            # Pydantic 模型
│   ├── database.py           # 引擎与会话
│   ├── auth.py               # JWT 认证
│   ├── routers/
│   │   ├── brainstorm.py     # 讨论、音频上传、世界观设定、设定图
│   │   ├── audio.py          # 转写处理与转写记录
│   │   ├── summary.py        # 摘要生成、设定提取、下载
│   │   └── email.py          # 邮件发送与发送日志
│   ├── services/
│   │   ├── whisper_service.py
│   │   ├── pyannote_service.py
│   │   ├── openai_service.py
│   │   └── email_service.py
│   ├── templates/summary_email.html
│   └── tests/                # pytest（冒烟）
├── frontend/                 # 原生 HTML/CSS/JS 单页前端
├── requirements.txt          # 后端运行所需（轻量）
├── requirements-ml.txt       # Whisper / pyannote / torch 等重型可选依赖
├── .env.example
├── CLAUDE.md                 # 工程规则
└── README.md
```

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env      # 填入 OPENAI_API_KEY / SMTP_* / HF_TOKEN 等
```

重型模型依赖（Whisper / pyannote / torch）不装也能启动：未安装或未配置 Key 时，
后端走离线分支，不发起任何网络请求。

## 运行

```bash
uvicorn backend.main:app --reload      # 仓库根目录
```

浏览器打开 `http://localhost:8000`。测试：

```bash
cd backend
python -m pytest
```

---

## 行为规格（验收标准）

以下每一条都是验收点。实现必须与规格一致，而不是只与末尾「已知问题」里举的例子一致。

### A. 认证与基础接口（不得回归）

- **A1** `POST /register` 用 JSON `{email, name, password}` 注册；邮箱重复返回 400。
- **A2** `POST /token` 用表单 `username`/`password` 换取 `{access_token, token_type}`；
  未认证访问受保护接口返回 401。
- **A3** `GET /users/me` 返回当前用户。
- **A4** 讨论、世界观设定、设定图、转写、摘要、邮件日志一律按 `owner_id` 隔离：
  访问他人资源不得返回数据。
- **A5** 资源不存在返回 404；请求体不合法返回 400/422，不得 500。

### B. 音频上传与落盘

- **B1** `POST /api/brainstorm/discussions/{id}/upload-audio` 只接受
  `wav / mp3 / m4a / flac / aac` 五种扩展名（大小写不敏感）；无扩展名或其它扩展名
  （如 `.exe` / `.txt`）必须返回 400，且响应体带 JSON 错误信息，不得落库、不得落盘。
- **B2** 落盘文件名必须由服务端安全化：去掉客户端传来的任何路径成分，只保留 basename，
  并保证最终写入路径始终位于上传目录内。即使客户端文件名形如
  `../../../../escaped.wav`，也不得在上传目录之外产生文件。
- **B3** 数据库中的 `filename` 字段保存**展示用的原始文件名**（不得被清洗成空串或只剩扩展名，
  中文名如 `第一幕讨论.wav` 必须原样保留）；`file_path` 是服务端实际落盘路径。
- **B4** 同名文件重复上传不得互相覆盖：两次上传的 `file_path` 必须不同，两个文件都要在磁盘上存在。

### C. 转写处理

- **C1** `POST /api/audio/process` 触发转写；转写结果（`full_text` 与逐段
  `speaker_label / start_time / end_time / text`）必须能通过
  `GET /api/audio/transcripts/{discussion_id}` 与
  `GET /api/audio/transcripts/{transcript_id}/segments` 读回。
- **C2** **幂等**：同一个 `audio_file_id` 重复调用 `POST /api/audio/process`，
  不得产生第二条转写记录。已有转写记录时直接复用，不重复插入转写与分段。
- **C3** **状态可见**：转写记录必须带 `status` 字段，取值为
  `pending` / `processing` / `completed` / `failed`：
  - 只有真正产出了 `full_text` 与分段才允许是 `completed`；
  - 处理失败必须是 `failed`，并且 `error_message` 非空（说明失败原因）；
  - 不允许「接口返回成功、后台静默失败、调用方永远看不到结果」。
- **C4** 转写失败不得把半成品写库：失败时该 `audio_file_id` 的转写记录不得处于 `completed`，
  也不得留下重复记录。

### D. 摘要生成与世界观设定提取

- **D1** `POST /api/summary/generate` 触发摘要生成，`GET /api/summary/{discussion_id}` 读回摘要。
- **D2** **状态可见**：摘要记录必须带 `status`（取值同上）与 `error_message`。
  只有真正拿到模型结果、摘要内容非空时才允许 `completed`；
  模型未配置、未安装或调用失败时必须 `failed` 且 `error_message` 非空，
  不得把失败伪装成成功，也不得静默丢弃。
- **D3** 生成的 Markdown（`markdown_content`）中「生成时间」必须是真实时间
  （形如 `2026-09-29 13:28:10`），不得出现 `{datetime.now()...}` 这类未展开的字面文本。
- **D4** 分节抽取必须稳健：`技术原理` / `社会结构` 三节内容既可能写成
  `## 技术原理` 标题行，也可能写成 `## 技术原理：正文`（正文跟在同一行）、
  `**技术原理**`（加粗小标题）。三种写法都必须能抽出该节正文，
  `tech_principles` / `social_structure` 不得整节为空。
- **D5** `POST /api/summary/extract-settings/{discussion_id}` 从转写分段里提取世界观设定
  并落库；模型返回的内容可能带 ```json 代码块围栏，必须能正常解析出设定条目
  （`category / key / value / description / owner_name`），返回 `extracted_count > 0`。
- **D6** 摘要的 `timeline` 必须从 ```json 围栏里解析成事件数组（每项含
  `year / event / description`）；解析不出来时退化为空数组，不得抛错。

### E. 邮件发送

- **E1** `POST /api/email/send-summary` 发送成功时返回 200 且 `status == "success"`，
  并为每个收件人写一条 `EmailLog`（`status == "success"`）。
- **E2** 发送失败时不得返回 2xx：必须返回 **502**，响应体 `status == "error"`
  且带非空 `error_message`；同时为每个收件人写一条失败日志，
  `EmailLog.status` 标记为失败且 `EmailLog.error_message` 非空（失败原因必须留痕）。
- **E3** `POST /api/email/send-notification` 必须接受 JSON 请求体
  `{recipients, subject, message}`，不得要求调用方改用 query 参数。

### F. 不得回归

- **F1** `README` 中 A 节列出的认证与基础接口、世界观设定与设定图的增查接口，
  以及 `GET /api/summary/{discussion_id}` 的时间倒序返回，都必须保持原有行为。
- **F2** `backend/tests/test_smoke.py` 冒烟测试必须全绿。
- **F3** 只使用 `requirements.txt` / `requirements-dev.txt` 里已声明的依赖，
  不联网、不调用真实的外部 API。

---

## 已知问题（不完整，只列举了部分现象）

最近在真实使用中暴露出一批缺陷，下面只是其中一部分现象，**不要只修这几条**，
以「行为规格」为准：

1. 上传音频时任意文件都能传成功；文件名里带 `..\..\` 时，文件会落到上传目录之外。
2. 同一条录音点两次「上传音频 / 转写」，转写记录会翻倍。
3. 没装 Whisper、没配 Key 的机器上，页面的转写记录永远停在「处理中」，看不到失败原因。
4. 生成的纲要 Markdown 里「生成时间」显示成一串 `{datetime.now()...}` 字面文本。
5. 「从讨论中提取设定」经常返回 0 条，明明讨论里出现了明确的设定。
