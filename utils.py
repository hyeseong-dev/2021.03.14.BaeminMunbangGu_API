import jwt
from json import JSONDecodeError

from django.http import JsonResponse

from my_settings import SECRET_KEY
from user.models import User

def login_decorator(func):
    def wrapper(self, request, *args, **kwargs ):
        try: 
            access_token = request.headers['Authorization']
            payload      = jwt.decode(access_token, SECRET_KEY, algorithms='HS256')
            user         = User.objects.get(pk=payload['user_pk'])
            request.user = user

            return func(self, request, *args, **kwargs)

        except jwt.exceptions.DecodeError:
            return JsonResponse({'message': 'INVALID_TOKEN'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
    return wrapper
