from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.conf import settings

from .models import Post
from .models import Group
from .models import Follow
from .models import User
from .models import Comment
from .forms import PostForm
from .forms import CommentForm


def paginator(post_list, num_disp, request):
    return Paginator(
        post_list, num_disp
    ).get_page(request.GET.get('page'))


def index(request):
    '''Представление главной старницы'''
    template = 'posts/index.html'
    post_list = Post.objects.all()
    num_disp = settings.NUM_DISP_POSTS_INDEX
    page_obj = paginator(post_list, num_disp, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    '''
    Представление страницы с сообществами
    Cтраница, на которой будут посты, отфильтрованные по группам.
    '''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    num_disp = settings.NUM_DISP_POSTS_GR_POSTS
    page_obj = paginator(post_list, num_disp, request)
    context = {
        'group': group,
        'slug': slug,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    '''Представление страницы профайла'''
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    count_user_posts = post_list.count()
    num_disp = settings.NUM_DISP_POSTS_PROFILE
    page_obj = paginator(post_list, num_disp, request)
    context = {
        'username': user,
        'page_obj': page_obj,
        'count_user_posts': count_user_posts
    }
    if not request.user.is_anonymous:
        follower_user = request.user
        if Follow.objects.filter(user=follower_user, author=user):
            following = True
        else:
            following = False
        context['following'] = following
    return render(request, template, context)


def post_detail(request, post_id):
    '''Представление отдельного поста'''
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    count_user_posts = post.author.posts.count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'count_user_posts': count_user_posts,
        'username': request.user,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    '''Страница создания поста'''
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=post.author)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    '''Страница редактирования поста'''
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user == post.author:
        if request.method == 'POST' and form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id)
        context = {
            'post': post,
            'form': form,
            'is_edit': is_edit,
        }
        return render(request, template, context)
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    '''Обработчик добавления комментария'''
    template = 'posts:post_detail'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(template, post_id=post_id)


@login_required
def follow_index(request):
    '''Страница с подписками'''
    template = 'posts/follow.html'
    follower_user = request.user
    # Проверяем что есть подписки
    if Follow.objects.filter(user=follower_user).exists():
        following_authors = Follow.objects.filter(
            user=follower_user
        ).values('author')
        # Проверяем что у авторов, на которых подписаны, есть посты
        post_list = Post.objects.filter(author__in=following_authors)
        if post_list.count() > 0:
            num_disp = settings.NUM_DISP_FOLLOW
            page_obj = paginator(post_list, num_disp, request)
            context = {
                'page_obj': page_obj,
                'subscription': 'posts_found',
            }
        else:
            context = {'subscription': 'zero_posts'}
    else:
        context = {
            'subscription': 'zero_authors',
        }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    '''Подписаться на Автора'''
    user_request = request.user
    author = get_object_or_404(User, username=username)
    # Если пользователь и есть автор
    if author == user_request:
        return redirect('posts:profile', username=author.username)
    else:
        # Ищем связь-подписку, если нет создаем
        Follow.objects.get_or_create(
            user=user_request,
            author=author,
        )
        return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    '''Отписка от Автора'''
    user_request = request.user
    author = get_object_or_404(User, username=username)
    if author == user_request:
        return redirect('posts:profile', username=author.username)
    else:
        if Follow.objects.filter(user=user_request, author=author).exists():
            Follow.objects.get(user=user_request, author=author).delete()
        return redirect('posts:profile', username=author.username)
