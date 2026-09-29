import os

try:  # 可选依赖：SDK 缺失时后端仍可导入，走离线分支
    from openai import OpenAI

    OPENAI_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于运行环境
    OpenAI = None
    OPENAI_SDK_AVAILABLE = False
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime

load_dotenv()


class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        # 未配置 Key / 未安装 SDK 时不建 client（离线分支），后端仍可启动。
        self.client = OpenAI(api_key=self.api_key) if (self.api_key and OPENAI_SDK_AVAILABLE) else None

    def generate_summary(
        self,
        transcript_text: str,
        discussion_title: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        base_prompt = f"""
你是一位专业的科幻小说世界观构建专家。请基于以下头脑风暴讨论内容，生成一份详细的世界观设定摘要。

讨论主题：{discussion_title}

讨论内容：
{transcript_text}

请输出以下内容：
1. 技术原理：详细描述世界观中的核心科技、物理规则、能量体系等
2. 社会结构：描述社会阶层、政治体系、经济模式、文化特征等
3. 时间线：生成一个包含关键事件的时间线，格式为JSON数组，每个事件包含year, event, description字段
4. 核心设定摘要：简要总结整个世界观的核心要点

请用Markdown格式输出，确保内容专业、逻辑清晰、富有科幻想象力。
"""

        if custom_prompt:
            base_prompt += f"\n\n额外要求：{custom_prompt}"

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位专业的科幻小说世界观构建专家，擅长从讨论中提炼核心设定并组织成结构化的世界观纲要。"},
                {"role": "user", "content": base_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        content = response.choices[0].message.content

        tech_principles = self._extract_section(content, "技术原理")
        social_structure = self._extract_section(content, "社会结构")
        timeline = self._extract_timeline(content)

        markdown_content = self._generate_markdown(
            discussion_title,
            content,
            tech_principles,
            social_structure,
            timeline
        )

        return {
            "content": content,
            "markdown_content": markdown_content,
            "tech_principles": tech_principles,
            "social_structure": social_structure,
            "timeline": timeline
        }

    def extract_world_settings(
        self,
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        settings = []

        for seg in transcript_segments:
            text = seg["text"]
            speaker = seg["speaker"]

            prompt = f"""
请从以下对话片段中提取科幻世界观设定。如果有明确的设定，请输出JSON格式的设定条目，否则输出空数组。

对话内容：
{text}

说话人：{speaker}

输出格式：
[
  {{
    "category": "角色|物理规则|科技|社会|地理|历史|其他",
    "key": "设定名称",
    "value": "设定内容",
    "description": "详细描述",
    "owner_name": "{speaker}"
  }}
]
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个精确的信息提取专家，善于从对话中提取结构化的世界观设定。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            try:
                extracted = json.loads(response.choices[0].message.content)
                if isinstance(extracted, list):
                    settings.extend(extracted)
            except json.JSONDecodeError:
                pass

        return settings

    def _extract_section(self, content: str, section_name: str) -> str:
        pattern = rf"##?\s*{section_name}[：:]?\s*\n(.*?)(?=##?\s|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_timeline(self, content: str) -> List[Dict[str, Any]]:
        pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(pattern, content)
        if match:
            try:
                timeline = json.loads(match.group(1))
                if isinstance(timeline, list):
                    return timeline
            except json.JSONDecodeError:
                pass

        events = []
        lines = content.split("\n")
        current_event = {}
        for line in lines:
            year_match = re.match(r"[-*]\s*(\d{4})\s*[-年]\s*(.+)", line)
            if year_match:
                if current_event:
                    events.append(current_event)
                current_event = {
                    "year": int(year_match.group(1)),
                    "event": year_match.group(2).strip(),
                    "description": ""
                }
            elif current_event and line.strip():
                current_event["description"] += line.strip() + " "
        if current_event:
            events.append(current_event)
        return events

    def _generate_markdown(
        self,
        title: str,
        content: str,
        tech_principles: str,
        social_structure: str,
        timeline: List[Dict[str, Any]]
    ) -> str:
        md = f"# {title} - 世界观设定纲要\n\n"
        md += f"**生成时间**: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}\n\n"

        md += "## 核心设定摘要\n\n"
        summary = self._extract_summary(content)
        md += summary + "\n\n"

        md += "## 技术原理\n\n"
        md += tech_principles + "\n\n"

        md += "## 社会结构\n\n"
        md += social_structure + "\n\n"

        md += "## 时间线\n\n"
        if timeline:
            md += "| 年份 | 事件 | 描述 |\n"
            md += "|------|------|------|\n"
            for event in timeline:
                year = event.get("year", "")
                event_text = event.get("event", "")
                description = event.get("description", "")
                md += f"| {year} | {event_text} | {description} |\n"
        else:
            md += "*暂无时间线数据*\n"

        return md

    def _extract_summary(self, content: str) -> str:
        pattern = r"##?\s*核心设定摘要[：:]?\s*\n(.*?)(?=##?\s|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return content[:500] + "..."
