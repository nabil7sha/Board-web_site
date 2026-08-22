from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse,Http404
from .models import Board
from django.contrib.auth.models import User
from .models import Topic,Post
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import UpdateView
from .models import Notification
from .forms import NewTopicForm,PostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Create your views here.

def home(request):

    boards = Board.objects.all()
    page = request.GET.get('page', 1)
    
    # عرض 6 بطاقات في كل صفحة (يمكنك تغيير الرقم)
    paginator = Paginator(boards, 12) 
    
    try:
        boards = paginator.page(page)
    except PageNotAnInteger:
        boards = paginator.page(1)
    except EmptyPage:
        boards = paginator.page(paginator.num_pages)
    return render(request,'home.html',{'boards':boards})


def board_topics(request,board_id):

    board = get_object_or_404(Board,pk=board_id)
    queryset = board.topics.order_by('-created_dt').annotate(comments=Count('post'))
    page = request.GET.get('page',1)
    paginator = Paginator(queryset,20)
    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        topics = paginator.page(1)
    except EmptyPage:
        topics = paginator.page(paginator.num_pages)

    return render(request,'topics.html',{'board':board,'topics':topics})



@login_required
def new_topic(request,board_id):
    board = get_object_or_404(Board,pk=board_id)
    if request.method == "POST":
        # تمت إضافة request.FILES لاستقبال الصورة
        form = NewTopicForm(request.POST, request.FILES) 
        if form.is_valid():
            topic = form.save(commit=False)
            topic.Board = board
            topic.created_by = request.user
            topic.save()

            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                created_by = request.user,
                topic=topic
            )
            return redirect('board_topics', board_id=board.pk)
    else:
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})



def topic_posts(request,board_id,topic_id):
     topic = get_object_or_404(Topic,Board__pk=board_id,pk=topic_id)  
     session_key = 'view_topic_{}'.format(topic.pk)
     if not request.session.get(session_key,False):
        topic.views +=1
        topic.save()
        request.session[session_key] = True
     return render(request,'topic_posts.html',{'topic':topic})



@login_required
def reply_topic(request, board_id,topic_id):
    topic = get_object_or_404(Topic, Board__pk=board_id, pk=topic_id)
    if request.method == "POST":
        form =PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()

            return redirect('topic_posts',board_id=board_id, topic_id = topic_id)
    else:
        form = PostForm()
    return render(request,'reply_topic.html',{'topic':topic,'form':form})



 
@method_decorator(login_required,name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message',)
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_dt = timezone.now()
        post.save()
        return redirect('topic_posts', board_id=post.topic.Board.pk, topic_id=post.topic.pk)


def about(request):

    return HttpResponse(request,"yes")
@login_required
def like_post(request, board_id, topic_id, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # إذا كان معجباً مسبقاً، نزيل الإعجاب ونحذف الإشعار
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        is_liked = False
        # حذف الإشعار عند إزالة الإعجاب
        Notification.objects.filter(to_user=post.created_by, from_user=request.user, notification_type='like', post=post).delete()
    
    # إذا لم يكن معجباً، نضيف الإعجاب ونرسل إشعاراً
    else:
        post.likes.add(request.user)
        is_liked = True
        
        # إنشاء إشعار (بشرط ألا يكون المستخدم قد أعجب بمنشور نفسه!)
        if request.user != post.created_by:
            Notification.objects.create(
                to_user=post.created_by,
                from_user=request.user,
                notification_type='like',
                post=post
            )
            
    return JsonResponse({
        'is_liked': is_liked,
        'likes_count': post.likes.count()
    })