"""测试夹具：把仓库根目录加入 sys.path，并为每个会话准备独立的临时数据库与目录。"""
import os
import pathlib
import sys
import tempfile

TESTS_DIR = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

for _p in (str(REPO_ROOT), str(BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 独立的临时库 / 上传目录 / 输出目录，避免污染工作区。
_TMP = tempfile.mkdtemp(prefix="scifi-brainstorm-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db").replace("\\", "/")
os.environ["BRAINSTORM_UPLOAD_DIR"] = os.path.join(_TMP, "uploads")
os.environ["BRAINSTORM_OUTPUT_DIR"] = os.path.join(_TMP, "outputs")
# 测试全程离线：清掉可能存在的真实凭据。
for _k in ("OPENAI_API_KEY", "SMTP_USER", "SMTP_PASSWORD", "HF_TOKEN"):
    os.environ.pop(_k, None)
