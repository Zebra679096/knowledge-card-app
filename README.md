# 知识卡片生成器 🎨

一个基于 Streamlit 的知识卡片生成工具，支持中英文自动识别，一键生成彩铅手绘风格知识卡片。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 功能特点

- 🎨 **彩铅手绘风格** - 生成可爱的手绘风格知识卡片
- 🗣️ **中英双语** - 自动检测语言，智能生成内容
- 🎯 **三模型对比** - 支持 Qwen / FLUX / Tongyi 三种生图模型
- 📱 **移动端适配** - 手机浏览器即可使用
- 🔒 **Key 本地存储** - API Key 只存在本地，不上传服务器
- ✏️ **文案可编辑** - 生成后可二次编辑文案再出图

## 快速开始

### 方式一：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/knowledge-card-app.git
cd knowledge-card-app

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行（首次会弹出浏览器）
streamlit run app.py
```

### 方式二：Streamlit Cloud 免费托管（推荐分享）

```bash
# 1. Fork 本仓库到你的 GitHub
# 2. 打开 https://streamlit.io/cloud
# 3. 关联你的 GitHub 仓库
# 4. 点击 Deploy!
# 5. 获得 https://xxx.streamlit.app 链接，直接分享给同事
```

## 获取 ModelScope API Key

1. 打开 [ModelScope](https://modelscope.cn) 注册/登录
2. 进入「设置」→「访问令牌」
3. 创建新令牌，复制 Key
4. 打开 App，在左侧边栏粘贴 Key

> 💡 一个 Key 同时用于 LLM 对话和生图，额度独立计算

## 使用流程

```
1. 填入 ModelScope API Key
      ↓
2. 输入知识点或粘贴文章内容
      ↓
3. 点击「生成对比文案」
      ↓
4.（可选）编辑文案
      ↓
5. 选择生图模型，点击「生成卡片」
      ↓
6. 下载使用
```

## 目录结构

```
knowledge-card-app/
├── app.py              # Streamlit 主应用（单文件）
├── requirements.txt    # Python 依赖
├── README.md           # 本文件
└── .gitignore         # Git 忽略文件
```

## 部署到 Streamlit Cloud

### 手动部署

1. 将 `app.py` 和 `requirements.txt` 推送到 GitHub 仓库
2. 打开 [streamlit.io/cloud](https://streamlit.io/cloud)
3. 点击 "New app"
4. 选择你的仓库和分支
5. Main file path 填写 `app.py`
6. 点击 Deploy

### 自动更新

当仓库代码更新后，Streamlit Cloud 会自动重新部署。

## API Key 配置说明

本 App **不会**上传你的 API Key 到任何服务器。

Key 的流向：
```
你的浏览器 → ModelScope API（直接请求）
                 ↓
            不经过任何中间服务器
```

## 生图模型说明

| 模型 | 速度 | 特点 | 推荐 |
|------|------|------|------|
| **Tongyi** | 最快（~27s） | 速度快，效果稳定 | ✅ 日常使用 |
| **FLUX** | 快（~19s） | 质量好，细节丰富 | 快速出图 |
| **Qwen** | 较慢（~150s） | 细节最丰富 | 追求质量 |

## 开发相关

```bash
# 本地调试
streamlit run app.py --server.headless false

# 查看所有配置
streamlit config show

# 指定端口
streamlit run app.py --server.port 8502
```

## License

MIT - 随意修改和使用

---

有问题欢迎提交 Issue 或 PR 🎨
