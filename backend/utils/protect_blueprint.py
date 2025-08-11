# utils/protect_blueprint.py

from utils.access_control import access_control

def protect_blueprint(bp, *, require_login=True, require_subscription=False, roles_allowed=None):
    """
    Оборачивает все view-функции Blueprint в декоратор access_control.
    Применяется до регистрации Blueprint в app.
    """
    for endpoint, view_func in bp.view_functions.items():
        protected_func = access_control(
            require_login=require_login,
            require_subscription=require_subscription,
            roles_allowed=roles_allowed
        )(view_func)
        bp.view_functions[endpoint] = protected_func
