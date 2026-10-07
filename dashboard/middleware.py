from functools import wraps

from django.core import signing
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.http import urlencode

from .mongodb import find_account_by_id, record_activity


SESSION_COOKIE = 'dashboard_session'
SESSION_SALT = 'balaji-os.account-session'
SESSION_MAX_AGE = 60 * 60 * 24 * 14


def account_for_request(request):
    token = request.COOKIES.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        session_data = signing.loads(
            token, salt=SESSION_SALT, max_age=SESSION_MAX_AGE
        )
    except signing.BadSignature:
        return None
    if not isinstance(session_data, dict):
        return None
    return find_account_by_id(session_data.get('account_id'))


class AccountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.account = account_for_request(request)
        is_public = (
            request.path == '/login/'
            or request.path.startswith('/static/')
        )
        if request.account is None and not is_public:
            if request.path.startswith('/api/'):
                response = JsonResponse(
                    {'error': 'Authentication required.'}, status=401
                )
            else:
                login_url = '/login/?' + urlencode({
                    'next': request.get_full_path(),
                })
                response = redirect(login_url)
        else:
            response = self.get_response(request)

        if request.account is not None and not request.path.startswith('/static/'):
            record_activity(
                request.account,
                action='Page request',
                method=request.method,
                path=request.path,
                status=response.status_code,
            )
        return response


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if getattr(request.account, 'role', None) != 'admin':
            return HttpResponseForbidden('Administrator access required.')
        return view_func(request, *args, **kwargs)
    return wrapped


def set_account_cookie(response, account_id, secure):
    token = signing.dumps(
        {'account_id': str(account_id)}, salt=SESSION_SALT, compress=True
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite='Lax',
    )
    return response
