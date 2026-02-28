from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.db.models.fields.files import FieldFile # 1. استدعاء مكتبة التعامل مع الملفات
from .models import AuditLog
from .middleware import get_current_user
import datetime

# 2. الدالة المساعدة المطورة (تحول التواريخ والملفات إلى نصوص)
def serialize_audit_data(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, FieldFile):  # إذا كان الحقل عبارة عن ملف
        return obj.name if obj.name else None # احفظ اسم الملف فقط
    elif isinstance(obj, dict):
        return {k: serialize_audit_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_audit_data(v) for v in obj]
    return obj


@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    if sender.__name__ in ['AuditLog', 'Session', 'LogEntry', 'ContentType']:
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # استخدام الدالة المطورة
            instance._old_values = serialize_audit_data(model_to_dict(old_instance))
        except sender.DoesNotExist:
            instance._old_values = None
    else:
        instance._old_values = None

@receiver(post_save)
def create_audit_log(sender, instance, created, **kwargs):
    if sender.__name__ in ['AuditLog', 'Session', 'LogEntry', 'ContentType']:
        return

    user = get_current_user()
    
    # استخدام الدالة المطورة
    new_values = serialize_audit_data(model_to_dict(instance))
    old_values = getattr(instance, '_old_values', None)

    action = 'CREATE' if created else 'UPDATE'

    if action == 'UPDATE' and old_values:
        changed_old = {}
        changed_new = {}
        for field, new_val in new_values.items():
            old_val = old_values.get(field)
            if str(old_val) != str(new_val):
                changed_old[field] = str(old_val)
                changed_new[field] = str(new_val)
        
        if not changed_old:
            return
            
        old_values = changed_old
        new_values = changed_new

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=sender.__name__,
        record_id=str(instance.pk),
        old_values=old_values,
        new_values=new_values
    )