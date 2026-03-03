import threading

_thread_locals = threading.local()

def get_current_user():
    """دالة مساعدة لجلب المستخدم من الصندوق السري"""
    user = getattr(_thread_locals, 'user', None)
    # الخدعة هنا: نتحقق أن المستخدم موجود وأنه ليس "AnonymousUser"
    if user and getattr(user, 'is_authenticated', False):
        return user
    return None

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. عند دخول الطلب: نضع كائن المستخدم في الصندوق
        _thread_locals.user = getattr(request, 'user', None)

        # 2. تمرير الطلب للنظام ليكمل عمله (Views)
        response = self.get_response(request)

        # 3. عند خروج الطلب: نفرغ الصندوق لمنع اختلاط البيانات
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user

        return response