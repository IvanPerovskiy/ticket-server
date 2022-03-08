from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.tokens import SlidingToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import TokenAuthentication as RestTokenAuthentication


class TokenAuthentication(RestTokenAuthentication):
    keyword = 'Bearer'


class JWTAuthentication(authentication.JWTAuthentication):
    def get_user(self, validated_token):
        try:
            return super().get_user(validated_token)
        except Exception:
            return None


class JWTControllerAuthentication(authentication.JWTAuthentication):
    """
    Авторизация для соединения с контроллером
    """
    def get_validated_token(self, raw_token):
        messages = []
        try:
            return SlidingToken(raw_token)
        except TokenError as e:
            messages.append({'token_class': SlidingToken.__name__,
                             'token_type': SlidingToken.token_type,
                             'message': e.args[0]})

        raise InvalidToken({
            'detail': _('Given token not valid for any token type'),
            'messages': messages,
        })
