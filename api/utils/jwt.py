from api.serializers import user_serializer
from datetime import datetime
from calendar import timegm
from rest_framework_jwt.settings import api_settings

def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': user_serializer.UserSerializer(user, context={'request': request}).data
    }
    
def jwt_payload_handler(payload, exp=None):

    if exp is not None:
        payload['exp'] = datetime.utcnow() + exp
    else:
        payload['exp'] = datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
        
    if hasattr(payload, 'user_id'):
        payload['user_id'] = user.email
    if hasattr(payload, 'email'):
        payload['email'] = user.email

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload
    