import os
from dotenv import load_dotenv
from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
import markdown

load_dotenv()


class EmailService:
    def __init__(self):
        # 未配置 SMTP_USER 时用占位发件地址，保证模块可导入（真正发信仍会走失败分支）。
        smtp_user = os.getenv("SMTP_USER", "")
        self.conf = ConnectionConfig(
            MAIL_USERNAME=smtp_user,
            MAIL_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
            MAIL_FROM=smtp_user or "noreply@example.com",
            MAIL_PORT=int(os.getenv("SMTP_PORT", "587")),
            MAIL_SERVER=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            MAIL_FROM_NAME="科幻创作头脑风暴系统",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )

        template_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "templates"
        )
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    async def send_summary_email(
        self,
        recipients: List[str],
        subject: str,
        summary_content: str,
        markdown_content: str,
        discussion_title: str,
        tech_principles: str,
        social_structure: str,
        timeline: List[dict]
    ) -> dict:
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code']
        )

        template = self.jinja_env.get_template("summary_email.html")
        body = template.render(
            discussion_title=discussion_title,
            summary_content=summary_content,
            html_content=html_content,
            tech_principles=tech_principles,
            social_structure=social_structure,
            timeline=timeline
        )

        message = MessageSchema(
            subject=subject or f"[世界观设定] {discussion_title}",
            recipients=recipients,
            body=body,
            subtype="html"
        )

        try:
            fm = FastMail(self.conf)
            await fm.send_message(message)
            return {
                "status": "success",
                "recipients": recipients,
                "message": "Email sent successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "recipients": recipients,
                "error": str(e)
            }

    async def send_notification(
        self,
        recipients: List[str],
        subject: str,
        message: str
    ) -> dict:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">{subject}</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <p style="line-height: 1.6; color: #333;">{message}</p>
            </div>
            <p style="margin-top: 20px; color: #7f8c8d; font-size: 12px;">
                此邮件由科幻创作头脑风暴系统自动发送
            </p>
        </div>
        """

        message_schema = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html_content,
            subtype="html"
        )

        try:
            fm = FastMail(self.conf)
            await fm.send_message(message_schema)
            return {
                "status": "success",
                "message": "Notification sent successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
