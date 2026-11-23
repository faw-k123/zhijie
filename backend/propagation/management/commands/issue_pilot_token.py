"""服务端签发六国实测访问令牌。

示例：
    python manage.py issue_pilot_token operator1 operator
    python manage.py issue_pilot_token reviewer1 approver
"""

from django.core.management.base import BaseCommand, CommandError

from api.pilot_auth import VALID_ROLES, issue_token


class Command(BaseCommand):
    help = "签发六国实测 API 访问令牌（角色：operator/approver/admin）"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", choices=sorted(VALID_ROLES))

    def handle(self, *args, **options):
        username = options["username"].strip()
        role = options["role"]
        if not username:
            raise CommandError("username 不能为空")
        token = issue_token(username, role)
        self.stdout.write(token)
