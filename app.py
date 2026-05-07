#!/usr/bin/env python3
"""
知识卡片生成器 - Streamlit 单文件版
DeepSeek-TUI vs OpenClaw vs 豆包 对比卡片
使用方法: streamlit run app.py
"""
import os
import sys
import time
import json
import re
import requests
from datetime import datetime

import streamlit as st

# ==============================
# ModelScope API 配置
# ==============================
MODESCOPE_API_KEY = ""  # 用户侧边栏填入
MODESCOPE_BASE_URL = "https://api-inference.modelscope.cn/"

MODELS = [
    {"model": "Qwen/Qwen-2-2/-Qwen2-2", "name": "Qwen"},
    {"model": "MusePublic/489_ckpt_FLUX_1", "name": "FLUX"},
    {"model": "Tongyi-MAI/Z-Image-Turbo", "name": "Tongyi"},
]

# ==============================
# 页面配置
# ==============================
st.set_page_config(
    page_title="知识卡片生成器",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# 自定义样式（移动端友好）
# ==============================
st.markdown("""
<style>
    .stApp { max-width: 100%; }
    .main-card { background: #faf8f5; border-radius: 16px; padding: 20px; margin: 10px 0; }
    .result-card { background: white; border-radius: 12px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    .stTextArea textarea { font-size: 16px; }
    .success-box { background: #e8f5e9; padding: 12px; border-radius: 8px; margin: 10px 0; }
    .error-box { background: #ffebee; padding: 12px; border-radius: 8px; margin: 10px 0; }
    .info-box { background: #e3f2fd; padding: 12px; border-radius: 8px; margin: 10px 0; }
    .analysis-box { background: #fff3e0; padding: 16px; border-radius: 12px; margin: 12px 0; border-left: 4px solid #ff9800; }
    @media (max-width: 768px) {
        h1 { font-size: 1.3rem !important; }
        h2 { font-size: 1.1rem !important; }
        .main-card { padding: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# 侧边栏 - API Key 配置
# ==============================
with st.sidebar:
    st.markdown("## ⚙️ 配置")

    api_key_input = st.text_input(
        "🔑 ModelScope API Key",
        value="",
        type="password",
        help="从 ModelScope 控制台获取: https://modelscope.cn/my/settings/key"
    )

    with st.expander("📖 Key 获取教程"):
        st.markdown("""
        **步骤：**
        1. 打开 [ModelScope](https://modelscope.cn)
        2. 登录 → 右上角头像 → 设置
        3. 点击「访问令牌」→ 创建新令牌
        4. 复制生成的 Key 填入左侧
        """)

    selected_model = st.selectbox(
        "🎨 生图模型",
        options=[m["name"] for m in MODELS],
        index=2,
        help="Tongyi 速度最快，FLUX 质量好，Qwen 细节丰富"
    )

    st.markdown("---")
    st.markdown("### 💡 使用流程")
    st.markdown("""
    1. 填入 ModelScope Key
    2. 输入知识点或文章
    3. AI 自动分析输入类型
    4. 生成对比文案（或单卡片）
    5. 一键生成知识卡片
    6. 下载使用
    """)

    st.markdown("---")
    st.markdown(
        "📄 **知识卡片生成器**  \n"
        "基于 ModelScope API  \n"
        "支持中英文自动识别"
    )

# ==============================
# Helper: 检测语言
# ==============================
def detect_language(text: str) -> str:
    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_count = len(re.findall(r'[a-zA-Z]', text))
    if chinese_count > english_count:
        return "中文"
    return "English"

# ==============================
# Helper: 分析用户输入（第一阶段）
# ==============================
def analyze_input(text: str, api_key: str) -> dict:
    if not api_key:
        raise ValueError("请先在侧边栏填入 ModelScope API Key")

    system_prompt = "你是一个知识整理分析助手。分析用户的输入，严格按JSON格式输出6个字段：\n\n1. **input_type**: \"detailed\"=用户输入了详细描述/段落 | \"keywords\"=用户只输入了关键词/词组/很短的内容\n\n2. **subject_count**: 检测到的主题/对比对象数量（数字，至少为1）\n\n3. **subjects**: 检测到的主题名称列表，如 [\"豆包\",\"DeepSeek-TUI\",\"OpenClaw\"]，如果输入是纯描述没有明确名称则从描述中推断\n\n4. **card_type**: \"comparison\"=多栏对比卡片（2个以上主题） | \"single\"=单主题知识卡片（1个主题）\n\n5. **analysis_note**: 一句话说明分析结论，例如\"用户输入了3个AI工具的详细描述，适合做对比卡片\"\n\n6. **input_summary**: 20字以内总结用户输入的核心主题\n\n严格输出纯JSON，不要任何markdown代码块包裹。"

    user_prompt = "用户输入内容:\n" + text[:2000]

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/DeepSeek-V4-Flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.1
    }

    resp = requests.post(
        MODESCOPE_BASE_URL + "v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    if resp.status_code != 200:
        raise Exception("分析API错误: " + str(resp.status_code))

    result = resp.json()
    choices = result.get("choices", [])
    if not choices:
        raise Exception("分析返回为空: " + str(result)[:200])

    content_str = choices[0].get("message", {}).get("content", "")
    if not content_str:
        raise Exception("分析内容为空")

    try:
        match = re.search(r'\{.*\}', content_str, re.DOTALL)
        if match:
            analysis = json.loads(match.group())
            required = ["input_type", "subject_count", "subjects", "card_type", "analysis_note", "input_summary"]
            for field in required:
                if field not in analysis:
                    raise Exception("分析结果缺少字段: " + field)
            return analysis
    except json.JSONDecodeError as e:
        raise Exception("分析JSON解析失败: " + str(e) + ", 原始: " + content_str[:200])

    raise Exception("分析结果格式错误: " + content_str[:200])


# ==============================
# Helper: 生成卡片内容（第二阶段）
# ==============================
def generate_content(text: str, api_key: str, analysis: dict) -> dict:
    card_type = analysis.get("card_type", "comparison")
    subjects = analysis.get("subjects", [])
    input_type = analysis.get("input_type", "detailed")

    # 卡片内容强制输出中文，不管用户输入什么语言
    if card_type == "single":
        # ==================== 单主题卡片 ====================
        system_prompt = "你是一个知识卡片生成助手。用户输入了一个主题，请生成一张知识卡片的内容。\n\n重要：无论用户输入什么语言，输出内容必须全部是中文！\n\n输出格式（严格纯JSON）：\n{\n  \"title\": \"卡片标题（中文）\",\n  \"subtitle\": \"副标题/一句话定义（中文）\",\n  \"icon\": \"主题图标emoji\",\n  \"label\": \"简短标签（5字内，中文）\",\n  \"points\": [\n    {\"title\": \"要点标题（中文）\", \"desc\": \"要点说明（15字内，中文）\", \"icon\": \"图标emoji\"},\n    {\"title\": \"要点标题（中文）\", \"desc\": \"要点说明（15字内，中文）\", \"icon\": \"图标emoji\"},\n    {\"title\": \"要点标题（中文）\", \"desc\": \"要点说明（15字内，中文）\", \"icon\": \"图标emoji\"},\n    {\"title\": \"要点标题（中文）\", \"desc\": \"要点说明（15字内，中文）\", \"icon\": \"图标emoji\"}\n  ],\n  \"tags\": [\"中文标签1\", \"中文标签2\", \"中文标签3\"],\n  \"bottom_note\": \"底部总结一句话（中文）\"\n}\n\n注意：所有JSON字段值必须全部是中文，points固定4个要点，desc不超过15字，tags固定3个标签，输出纯JSON不要markdown代码块。"

        user_prompt = "用户主题:\n" + text[:2000] + "\n推断主题名: " + (subjects[0] if subjects else "未知") + "\n\n注意：卡片所有内容（title/subtitle/label/points/tags/bottom_note）必须全部输出中文。"

    else:
        # ==================== 多栏对比卡片 ====================
        subject_list = " / ".join(subjects[:5])

        if input_type == "detailed":
            system_prompt = ("你是一个知识对比卡片生成助手。用户提供了" + str(len(subjects)) + "个主题的详细描述，请提取核心特征生成对比卡片。\n\n"
                             "重要：无论用户输入什么语言，输出内容必须全部是中文！\n\n"
                             "主题列表: " + subject_list + "\n\n"
                             "输出格式（严格纯JSON）：\n"
                             "{\n"
                             "  \"title\": \"对比标题（中文）\",\n"
                             "  \"items\": [\n"
                             "    {\"name\": \"主题1名称（中文）\", \"icon\": \"emoji\", \"label\": \"中文标签\", \"points\": [\"中文要点1(10字内)\", \"中文要点2(10字内)\", \"中文要点3(10字内)\"]},\n"
                             "    {\"name\": \"主题2名称（中文）\", \"icon\": \"emoji\", \"label\": \"中文标签\", \"points\": [\"中文要点1(10字内)\", \"中文要点2(10字内)\", \"中文要点3(10字内)\"]}\n"
                             "  ],\n"
                             "  \"bottom_note\": \"底部总结（15字内，中文）\"\n"
                             "}\n\n"
                             "规则：所有JSON字段值必须全部是中文，points固定3个要点每点不超过10字，输出纯JSON不要markdown代码块。")

            user_prompt = "主题: " + subject_list + "\n\n用户详细描述:\n" + text[:2500] + "\n\n注意：卡片所有内容（title/label/points/bottom_note）必须全部输出中文，points固定3个要点每点不超过10字，输出纯JSON。"

        else:
            system_prompt = ("你是一个知识对比卡片生成助手。用户只提供了" + str(len(subjects)) + "个关键词/短句，请为每个主题补充核心特征。\n\n"
                             "重要：无论用户输入什么语言，输出内容必须全部是中文！\n\n"
                             "主题列表: " + subject_list + "\n\n"
                             "输出格式（严格纯JSON）：\n"
                             "{\n"
                             "  \"title\": \"对比标题（中文）\",\n"
                             "  \"items\": [\n"
                             "    {\"name\": \"主题1名称（中文）\", \"icon\": \"emoji\", \"label\": \"中文标签\", \"points\": [\"中文要点1(10字内)\", \"中文要点2(10字内)\", \"中文要点3(10字内)\"]},\n"
                             "    {\"name\": \"主题2名称（中文）\", \"icon\": \"emoji\", \"label\": \"中文标签\", \"points\": [\"中文要点1(10字内)\", \"中文要点2(10字内)\", \"中文要点3(10字内)\"]}\n"
                             "  ],\n"
                             "  \"bottom_note\": \"底部总结（15字内，中文）\"\n"
                             "}\n\n"
                             "规则：所有JSON字段值必须全部是中文，根据关键词推断核心特征，points固定3个要点每点不超过10字，输出纯JSON不要markdown代码块。")

            user_prompt = "用户关键词:\n" + text[:1000] + "\n\n注意：卡片所有内容（title/label/points/bottom_note）必须全部输出中文，根据关键词推断每个主题的核心特征，points固定3个要点每点不超过10字，输出纯JSON。"

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/DeepSeek-V4-Flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }

    resp = requests.post(
        MODESCOPE_BASE_URL + "v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120
    )

    if resp.status_code != 200:
        raise Exception("生成API错误: " + str(resp.status_code))

    result = resp.json()
    choices = result.get("choices", [])
    if not choices:
        raise Exception("生成返回为空: " + str(result)[:200])

    content_str = choices[0].get("message", {}).get("content", "")
    if not content_str:
        raise Exception("生成内容为空")

    try:
        match = re.search(r'\{.*\}', content_str, re.DOTALL)
        if match:
            data = json.loads(match.group())
            data["_analysis"] = analysis
            return data
    except json.JSONDecodeError as e:
        raise Exception("生成JSON解析失败: " + str(e) + ", 原始: " + content_str[:300])

    raise Exception("生成内容格式错误: " + content_str[:200])


# ==============================
# Helper: 生成图片
# ==============================
def generate_image(prompt: str, model_name: str, model_label: str, output_dir: str, api_key: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "card_" + model_label + "_" + str(int(time.time())) + ".png")

    negative_prompt = "no text, no words, no letters, no numbers, no writing, no symbols, no signage, clean image"
    full_prompt = prompt + ", " + negative_prompt

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }

    print("[" + model_label + "] 提交任务...")

    try:
        request_data = {
            "model": model_name,
            "prompt": full_prompt,
            "negative_prompt": negative_prompt,
            "width": 1024,
            "height": 1366,
        }

        resp = requests.post(
            MODESCOPE_BASE_URL + "v1/images/generations",
            headers={**headers, "X-ModelScope-Async-Mode": "true"},
            data=json.dumps(request_data, ensure_ascii=False).encode("utf-8"),
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        task_id = result.get("task_id")
        if not task_id:
            raise Exception("响应缺少 task_id: " + str(result))

        print("[" + model_label + "] Task ID: " + task_id + "，等待结果...")

        start = time.time()
        while time.time() - start < 300:
            result = requests.get(
                MODESCOPE_BASE_URL + "v1/tasks/" + task_id,
                headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
                timeout=30
            )
            data = result.json()
            status = data.get("task_status")
            elapsed = int(time.time() - start)
            print("[" + model_label + "] 状态: " + status + " (" + str(elapsed) + "s)")

            if status == "SUCCEED":
                image_url = (data.get("output_images") or data.get("input", {}).get("output_images") or [None])[0]
                if not image_url:
                    raise Exception("未找到图片URL")
                img_data = requests.get(image_url, timeout=60)
                img_data.raise_for_status()

                from PIL import Image
                from io import BytesIO
                image = Image.open(BytesIO(img_data.content))
                image.save(output_path)
                print("[" + model_label + "] ✅ 成功!")
                return output_path
            elif status == "FAILED":
                break
            time.sleep(4)

        raise Exception("生成超时")

    except Exception as e:
        raise Exception("[" + model_label + "] 生图失败: " + str(e))


# ==============================
# Helper: 构建生图 Prompt
# ==============================
def build_image_prompt(data: dict, card_type: str) -> str:
    if card_type == "single":
        title = data.get("title", "知识卡片")
        subtitle = data.get("subtitle", "")
        icon = data.get("icon", "📌")
        label = data.get("label", "")
        points = data.get("points", [])
        tags = data.get("tags", [])
        bottom = data.get("bottom_note", "")

        points_text = ""
        for p in points[:4]:
            t = p.get("title", "")
            d = p.get("desc", "")
            ic = p.get("icon", "•")
            points_text += f"{ic} {t}: {d}\n"

        tags_text = " / ".join(tags[:3])

        prompt = ('Full-color hand-drawn doodle knowledge card, colored pencil illustration style, vertical 3:4 format.\n\n'
                  'Title at top in large colorful hand-drawn Chinese calligraphy: "' + title + '"\n'
                  'Subtitle below: "' + subtitle + '"\n\n'
                  'Central icon: ' + icon + ' in a hand-drawn circle\n\n'
                  'Four key points arranged in a 2x2 grid with hand-drawn frames:\n' + points_text + '\n'
                  'Tags at bottom: ' + tags_text + '\n\n'
                  'Bottom ribbon: "' + bottom + '"\n\n'
                  'Style: soft wobbly black outlines, pastel crayon colors, light cream textured background, '
                  'colorful doodle illustrations, all Chinese labels in hand-drawn brush style, 4K high resolution.')
    else:
        items = data.get("items", [])
        items_text = ""
        for item in items:
            name = item.get("name", "")
            icon = item.get("icon", "📌")
            label = item.get("label", "")
            pts = item.get("points", [])[:3]
            pts_text = " / ".join(pts)
            items_text += icon + " " + name + ": " + pts_text + "\n"

        bottom = data.get("bottom_note", "")

        prompt = ('Full-color hand-drawn doodle knowledge card, colored pencil illustration style, vertical 3:4 format.\n\n'
                  'Title at top: "' + data.get("title", "对比") + '"\n\n'
                  'Two-column comparison layout with hand-drawn border frames:\n' + items_text + '\n'
                  'Bottom banner: "' + bottom + '"\n\n'
                  'Style: soft wobbly black outlines, pastel crayon colors, light cream textured background, '
                  'colorful doodle illustrations, Chinese labels in hand-drawn brush style, 4K high resolution.')

    return prompt


# ==============================
# 主界面
# ==============================
st.markdown("## 🎨 知识卡片生成器")

with st.expander("📖 使用说明", expanded=False):
    st.markdown("""
    **使用流程：**
    1. 在左侧填入 ModelScope API Key
    2. 输入知识点或粘贴文章内容
    3. 点击「AI 分析输入」→ 自动识别输入类型
    4. 查看分析结果，确认卡片类型
    5. 点击「生成卡片」→ 下载

    **支持语言：** 中文、English 自动识别
    **卡片类型：** 自动识别是对比卡片还是单主题卡片
    """)

# ==============================
# 步骤1: 输入内容
# ==============================
st.markdown("### 📝 步骤1：输入内容")

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_area(
        "输入知识点或文章内容",
        placeholder="支持两种输入方式：\n\n"
                    "① 详细描述：如「DeepSeek-TUI是终端编程工具，专注代码生成...」\n\n"
                    "② 关键词对比：如「DeepSeek-TUI vs OpenClaw vs 豆包」",
        height=200,
        help="支持中文或英文，详细描述会自动提取要点，关键词会补充特征"
    )
with col2:
    st.markdown("#### 或选示例")
    if st.button("📋 AI工具对比"):
        user_input = """DeepSeek-TUI: 终端编程工具，专为DeepSeek模型设计，键盘驱动TUI界面，支持文件编辑/Shell命令/Git管理/代码调试，需自备API Key，适合开发者本地使用

OpenClaw: 通用AI助手/Agent系统，多渠道接入（飞书/Telegram等），完整记忆系统（短期+长期+日志），支持定时任务/Cron调度/自动化执行，能发消息/操作文件/浏览网页/管理节点，专注自动化办公

豆包: 字节跳动对话AI应用，手机App/网页端使用，语音/图片/文字多模态交互，会话短期记忆，普通大众日常问答/聊天/娱乐，无执行能力纯对话"""

    if st.button("📋 单主题"):
        user_input = "深度学习"

    if st.button("📋 两个产品"):
        user_input = "飞书 vs 钉钉"

lang_display = ""
if user_input:
    lang_display = detect_language(user_input)
    st.info("🗣️ 检测语言: " + lang_display)

# ==============================
# 步骤2: AI 分析
# ==============================
api_key = api_key_input.strip()

st.markdown("### 🔍 步骤2：AI 分析输入类型")

if st.button("🤖 AI 分析输入", type="primary", disabled=not user_input or not api_key):
    if not api_key:
        st.error("❌ 请先在侧边栏填入 ModelScope API Key")
    elif not user_input.strip():
        st.error("❌ 请输入内容")
    else:
        with st.spinner("🤖 AI 分析中..."):
            try:
                analysis = analyze_input(user_input, api_key)
                st.session_state["analysis"] = analysis
                st.session_state["detected_lang"] = detect_language(user_input)
                st.success("✅ 分析完成！")
            except Exception as e:
                st.error("❌ 分析失败: " + str(e))
                st.session_state.pop("analysis", None)

# ==============================
# 展示分析结果
# ==============================
if "analysis" in st.session_state:
    analysis = st.session_state["analysis"]

    card_type = analysis.get("card_type", "comparison")
    input_type = analysis.get("input_type", "keywords")
    subject_count = analysis.get("subject_count", 0)
    subjects = analysis.get("subjects", [])
    analysis_note = analysis.get("analysis_note", "")
    input_summary = analysis.get("input_summary", "")

    # 分析结果展示
    st.markdown("#### 📊 分析结果")

    col_a, col_b = st.columns(2)
    with col_a:
        ct_emoji = "📊" if card_type == "comparison" else "📄"
        ct_label = "对比卡片" if card_type == "comparison" else "单主题卡片"
        st.markdown("**卡片类型：** " + ct_emoji + " " + ct_label)

        it_emoji = "📝" if input_type == "detailed" else "🏷️"
        it_label = "详细描述" if input_type == "detailed" else "关键词/短句"
        st.markdown("**输入类型：** " + it_emoji + " " + it_label)

    with col_b:
        st.markdown("**主题数量：** " + str(subject_count))
        st.markdown("**主题列表：** " + " / ".join(subjects[:5]))

    st.markdown("**分析结论：** " + analysis_note)
    st.markdown("**核心主题：** " + input_summary)

    # 提示用户
    if input_type == "keywords":
        st.info("💡 检测到关键词输入，AI 将补充每个主题的核心特征后生成卡片")
    else:
        st.info("💡 检测到详细描述，AI 将从描述中提取关键特征生成卡片")

    # ==============================
    # 步骤3: 生成内容
    # ==============================
    st.markdown("### ✍️ 步骤3：生成卡片内容")

    if st.button("📝 生成内容", type="secondary"):
        with st.spinner("🤖 AI 生成中..."):
            try:
                result = generate_content(user_input, api_key, analysis)
                st.session_state["knowledge_data"] = result
                st.success("✅ 内容生成成功！")
            except Exception as e:
                st.error("❌ 生成失败: " + str(e))
                st.session_state.pop("knowledge_data", None)

# ==============================
# 步骤4: 展示文案 & 生图
# ==============================
if "knowledge_data" in st.session_state:
    data = st.session_state["knowledge_data"]
    analysis = data.get("_analysis", {})
    card_type = analysis.get("card_type", "comparison")
    lang = st.session_state.get("detected_lang", "中文")

    st.markdown("#### " + data.get("title", "生成结果"))

    if card_type == "single":
        # 单主题卡片展示
        st.markdown("**" + data.get("subtitle", "") + "**")

        cols = st.columns(2)
        for i, p in enumerate(data.get("points", [])[:4]):
            with cols[i % 2]:
                st.markdown(data.get("icon", "📌") + " **" + p.get("title", "") + "**: " + p.get("desc", ""))

        st.markdown("**标签：** " + " / ".join(data.get("tags", [])))
        if data.get("bottom_note"):
            st.markdown("> " + data.get("bottom_note"))
    else:
        # 对比卡片展示
        cols = st.columns(len(data.get("items", [])))
        for i, item in enumerate(data.get("items", [])):
            with cols[i]:
                st.markdown("##### " + item.get("icon", "📌") + " " + item.get("name", ""))
                st.markdown("**" + item.get("label", "") + "**")
                for pt in item.get("points", []):
                    st.markdown("- " + pt)

        if data.get("bottom_note"):
            st.markdown("> " + data.get("bottom_note"))

    # 文案编辑
    with st.expander("✏️ 编辑文案"):
        edited_title = st.text_input("标题", value=data.get("title", ""))
        if edited_title:
            data["title"] = edited_title

        if card_type == "single":
            edited_sub = st.text_input("副标题", value=data.get("subtitle", ""))
            if edited_sub:
                data["subtitle"] = edited_sub
            edited_bottom = st.text_input("底部总结", value=data.get("bottom_note", ""))
            if edited_bottom:
                data["bottom_note"] = edited_bottom
        else:
            for i, item in enumerate(data.get("items", [])):
                with st.expander("编辑: " + item.get("name", "")):
                    new_name = st.text_input("名称", value=item.get("name", ""), key="name_" + str(i))
                    new_icon = st.text_input("图标", value=item.get("icon", ""), key="icon_" + str(i))
                    new_label = st.text_input("标签", value=item.get("label", ""), key="label_" + str(i))
                    new_pts = st.text_area("要点（每行一个）", value="\n".join(item.get("points", [])), key="pts_" + str(i), height=80)
                    if new_name:
                        data["items"][i]["name"] = new_name
                    if new_icon:
                        data["items"][i]["icon"] = new_icon
                    if new_label:
                        data["items"][i]["label"] = new_label
                    if new_pts:
                        data["items"][i]["points"] = [p.strip() for p in new_pts.split("\n") if p.strip()]
            edited_bottom = st.text_input("底部总结", value=data.get("bottom_note", ""))
            if edited_bottom:
                data["bottom_note"] = edited_bottom

        st.session_state["knowledge_data"] = data
        st.success("✅ 文案已更新")

    # ==============================
    # 步骤5: 生成图片
    # ==============================
    st.markdown("### 🎨 步骤4：生成卡片图片")

    col_gen1, col_gen2 = st.columns([1, 3])
    with col_gen1:
        if st.button("🖼️ 生成卡片", type="primary"):
            model_info = next((m for m in MODELS if m["name"] == selected_model), MODELS[2])
            model_name = model_info["model"]
            model_label = model_info["name"]

            prompt = build_image_prompt(data, card_type)

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("[" + model_label + "] 提交生图任务...")
            progress_bar.progress(10)

            try:
                output_dir = "/tmp/knowledge_cards"
                status_text.text("[" + model_label + "] 等待生图完成...")
                progress_bar.progress(30)

                img_path = generate_image(prompt, model_name, model_label, output_dir, api_key)

                progress_bar.progress(100)
                status_text.text("✅ 生成成功!")

                st.markdown("#### 生成结果：")
                st.image(img_path, use_container_width=True)

                with open(img_path, "rb") as f:
                    img_bytes = f.read()

                filename = "知识卡片_" + data.get("title", "对比") + "_" + model_label + ".png"
                st.download_button(
                    label="📥 下载卡片图片",
                    data=img_bytes,
                    file_name=filename,
                    mime="image/png"
                )

                if "history" not in st.session_state:
                    st.session_state["history"] = []
                st.session_state["history"].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "title": data.get("title", ""),
                    "model": model_label,
                    "path": img_path
                })

            except Exception as e:
                progress_bar.progress(100)
                st.error("❌ 生成失败: " + str(e))

    with col_gen2:
        st.markdown("**生图模型：** " + selected_model)
        st.markdown("**卡片类型：** " + ("对比" if card_type == "comparison" else "单主题"))

# ==============================
# 历史记录
# ==============================
if "history" in st.session_state and st.session_state["history"]:
    st.markdown("---")
    st.markdown("### 📚 历史记录")
    for h in reversed(st.session_state["history"][-5:]):
        with st.expander(h["time"] + " - " + h["title"] + " (" + h["model"] + ")"):
            if os.path.exists(h["path"]):
                st.image(h["path"], use_container_width=True)
                with open(h["path"], "rb") as f:
                    st.download_button(
                        label="📥 下载",
                        data=f.read(),
                        file_name="知识卡片_" + h["title"] + "_" + h["model"] + ".png",
                        mime="image/png",
                        key="dl_" + h["time"]
                    )

# ==============================
# 页脚
# ==============================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 12px;'>"
    "🎨 知识卡片生成器 | 基于 ModelScope API | "
    "<a href='https://modelscope.cn' target='_blank'>ModelScope</a>"
    "</div>",
    unsafe_allow_html=True
)
