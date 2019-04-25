from django.contrib.auth.backends import ModelBackend
from .models import User
import re

def get_user_by_account(account):
    """
        根据用户名或手机号来查询user
        :param account: 手机号 、 用户名
        :return: None, user
        """
    try:
        if re.match(r'^1[3-9]\d{9}$',account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    # m
    except User.DoesNotExist:
        return None
    else:
        return user

class UsernameMobileAuthBackend(ModelBackend):
    """自定义Django的认证后端类"""
    print('haha')
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user


