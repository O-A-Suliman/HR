from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import AuditLog
from employees.models import Employee
from .middleware import get_current_user # استدعاء الدالة التي تفتح الصندوق

# ==========================================
# 1. الكاميرا الأولى: تعمل *قبل* الحفظ لتصوير البيانات القديمة
# ==========================================
@receiver(pre_save, sender=Employee)
def capture_old_data(sender, instance, **kwargs):
    # إذا كان الموظف لديه ID، فهذا يعني أنه مسجل مسبقاً (عملية تعديل)
    if instance.pk: 
        try:
            # نذهب لقاعدة البيانات ونجلب بياناته القديمة قبل أن تتغير
            old_data = sender.objects.get(pk=instance.pk)
            # نحتفظ بالبيانات القديمة داخل المتغير instance بشكل مؤقت
            instance._old_values = model_to_dict(old_data)
        except sender.DoesNotExist:
            instance._old_values = {}
    else:
        # إذا لم يكن له ID، فهذا موظف جديد تماماً، ولا يوجد له بيانات قديمة
        instance._old_values = {}


# ==========================================
# 2. الكاميرا الثانية: تعمل *بعد* الحفظ لتسجيل كل شيء في الدفتر
# ==========================================
@receiver(post_save, sender=Employee)
def log_the_action(sender, instance, created, **kwargs):
    # نفتح الصندوق لنعرف من هو المستخدم الذي قام بهذه العملية
    current_user = get_current_user()
    
    # نجهز البيانات الجديدة
    new_values = model_to_dict(instance)
    
    # نحدد هل العملية "إنشاء" أم "تعديل"
    if created:
        action_type = 'create'
        old_values = {}
    else:
        action_type = 'update'
        # نستدعي البيانات القديمة التي احتفظنا بها في الكاميرا الأولى
        old_values = getattr(instance, '_old_values', {})

    # أخيراً: نكتب كل هذه المعلومات في دفتر AuditLog الذي صنعته أنت
    AuditLog.objects.create(
        user=current_user if (current_user and current_user.is_authenticated) else None,
        action=action_type,
        model_name='Employee',
        record_id=instance.pk,
        old_values=old_values,
        new_values=new_values
    )