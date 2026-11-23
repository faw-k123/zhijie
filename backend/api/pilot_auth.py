"""六国实测的服务端身份与角色校验。

不信任请求体里的 approver/operator。令牌由项目服务端签发，
前端只持有令牌，不能自行声明角色。
"""

from __future__ import annotations

from django.core import signing
from rest_framework import status
from rest_framework.response import Response

SALT = "pilot-research-auth-v1"
VALID_ROLES = {"operator", "approver", "admin"}


def issue_token(username: str, role: str, *, max_age_seconds: int = 8 * 3600) -> str:
    if role not in VALID_ROLES:
        raise ValueError("invalid role")
    if not username:
        raise ValueError("username required")
    return signing.dumps(
        {"username": username, "role": role},
        salt=SALT,
        compress=True,
    )


def actor_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    try:
        payload = signing.loads(token, salt=SALT, max_age=8 * 3600)
    except (signing.BadSignature, signing.SignatureExpired):
        return None
    if not isinstance(payload, dict) or payload.get("role") not in VALID_ROLES:
        return None
    return payload


def require_roles(request, roles: set[str]):
    actor = actor_from_request(request)
    if actor is None:
        return None, Response(
            {"success": False, "message": "未登录或令牌无效"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if actor.get("role") not in roles and actor.get("role") != "admin":
        return None, Response(
            {"success": False, "message": "无权限执行该操作"},
            status=status.HTTP_403_FORBIDDEN,
        )
    return actor, None
