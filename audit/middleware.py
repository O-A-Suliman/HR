import threading

# 1. الصندوق السري (يتم تعريفه مرة واحدة في بداية الملف)
_thread_locals = threading.local()

# 2. النافذة الآمنة (الدالة التي ستقرأ من الصندوق وتستدعيها الـ Signals)
# كتبناها هنا في نفس الملف لكي تكون قريبة من الصندوق
def get_current_user():
    return getattr(_thread_locals, 'user', None)

# 3. موظف الاستقبال (الـ Middleware الذي يضع المستخدم في الصندوق وينظفه)
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # دخول الطلب: وضع المستخدم في الصندوق
        _thread_locals.user = getattr(request, 'user', None)
        
        # ترك الطلب يمر إلى الـ View
        response = self.get_response(request)
        
        # خروج الطلب: مسح المستخدم من الذاكرة المؤقتة
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response