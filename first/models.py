from django.db import models
from django.contrib.auth.models import User
from django.utils.text import Truncator

class Board(models.Model):

    name= models.CharField(max_length=50,unique=True)
    description=models.CharField(max_length=150)

    image = models.ImageField(upload_to='boards/', null=True, blank=True)

    def __str__ (self):
     return self.name

    def get_post_count(self):
        return Post.objects.filter(topic__Board=self).count()

    def get_last_post(self):
        return Post.objects.filter(topic__Board=self).order_by('-created_dt').first()


class Topic(models.Model):
    subject=models.CharField(max_length=150)
    Board=models.ForeignKey(Board,related_name='topics',on_delete=models.CASCADE)
    created_by=models.ForeignKey(User,related_name='topics',on_delete=models.CASCADE)
    created_dt=models.DateTimeField(auto_now_add=True)
    views=models.PositiveBigIntegerField(default=0)
    image = models.ImageField(upload_to='topics/', null=True, blank=True)
class Post(models.Model):
        message=models.TextField(max_length=4000)
        topic=models.ForeignKey(Topic,related_name='post',on_delete=models.CASCADE)
        created_by=models.ForeignKey(User,related_name='post',on_delete=models.CASCADE)
        created_dt=models.DateTimeField(auto_now_add=True)
        updated_dt = models.DateTimeField(null=True)
        def __str__(self):
         truncted_message = Truncator(self.message)
         return truncted_message.chars(30)


class Notification(models.Model):
    # الخيارات المتاحة للإشعار
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment')
    )
    
    # الشخص الذي سيستلم الإشعار (صاحب المنشور)
    to_user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    
    # الشخص الذي قام بالتفاعل (من ضغط إعجاب أو كتب تعليق)
    from_user = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    
    # نوع الإشعار (هل هو إعجاب أم تعليق؟)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # المنشور الذي حدث عليه التفاعل
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    
    # حالة الإشعار (هل شاهده المستخدم أم لا لكي نظهر النقطة الحمراء)
    is_read = models.BooleanField(default=False)
    
    # وقت حدوث الإشعار
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To: {self.to_user.username} | From: {self.from_user.username} | Type: {self.notification_type}"
# Create your models here.
