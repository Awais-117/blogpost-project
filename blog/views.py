from django.shortcuts import render, get_object_or_404, redirect
from .models import Post,Clap,Comment
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignupForm, ProfileForm
from blog.models import Profile
from .models import Follow
from django.utils.html import strip_tags
import json
from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# import os
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count


def landing(request):
    if request.user.is_authenticated:
        return redirect('home')   # posts page
    return render(request, 'blog/landing.html')


# -------------------------
# Home Page
# -------------------------
@login_required
def home(request):
    
    # Post.objects.filter(
    #     is_published=False,
    #     scheduled_at__lte=timezone.now()
    # ).update(is_published=True)
    # profile, created = Profile.objects.get_or_create(user=request.user)

    # if not profile.is_completed:
    #     return redirect("complete_profile")


    # posts = Post.objects.filter(
    #     is_published=True
    # ).select_related("author").order_by("-created_at")

    base_posts = Post.objects.filter(
        is_published=True
    ).select_related("author")

    for_you = base_posts.order_by("-created_at")

    trending = base_posts.annotate(
        clap_count=Count("claps")
    ).order_by("-views", "-clap_count")[:10]

    featured = base_posts.filter(
        is_featured=True
    ).order_by("-created_at")
    # posts = Post.objects.all()
    for post in base_posts:
        blocks = post.content.get("blocks", [])
        text_content = ""

        for block in blocks:
            # if block["type"] == "paragraph":
            if block["type"] in ["paragraph", "header"]:
                text_content += block["data"].get("text", "") + " "

            # elif block["type"] == "header":
                # text_content += block["data"].get("text", "") + " "

        post.rendered_excerpt = text_content.strip()
    return render(request, "blog/home.html", {
        "for_you": for_you,
        "trending":trending,
        "featured":featured
    })





def detail(request, id):
    post = get_object_or_404(Post, id=id)
    post.views += 1
    post.save(update_fields=["views"])
    
    if not post.is_published:
        if not request.user.is_authenticated or post.author != request.user:
            return HttpResponseForbidden("This post is still a draft.")

    clap_count = post.claps.count()
    comment_count = post.comments.count()
    comments = post.comments.select_related("user").order_by("-created_at")
    user_clapped = False

    if request.user.is_authenticated:
        user_clapped = Clap.objects.filter(
            post=post,
            user=request.user
        ).exists()
        
        
    is_following = False
    followers_count = 0

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=post.author
        ).exists()

    followers_count = Follow.objects.filter(
        following=post.author
    ).count()   

    return render(request, 'blog/detail.html', {
        'post': post,
        'clap_count': clap_count,
        'comment_count': comment_count,
        'comments': comments,
        'user_clapped': user_clapped,
        
         # 🔥 NEW
        'is_following': is_following,
        'followers_count': followers_count,
    })
    



@login_required
def add_comment(request, id):
    post = get_object_or_404(Post, id=id)

    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )
            
        return JsonResponse({
                "id": comment.id,
                "username": comment.user.username,
                "content": comment.content,
                # "time": "Just now",
                "created_at": comment.created_at.isoformat(),
                "comment_count": post.comments.count()
            })

    return JsonResponse({"error": "Invalid request"}, status=400)    

    




@login_required
@require_POST
def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id)

    if comment.user != request.user:
        return JsonResponse({"error": "Forbidden"}, status=403)

    post = comment.post
    comment.delete()
    
    return JsonResponse({
        "comment_count": post.comments.count()
    })
@login_required
def toggle_clap(request, id):
    post = get_object_or_404(Post, id=id)

    clap, created = Clap.objects.get_or_create(
        post=post,
        user=request.user
    )

    if not created:
        clap.delete()
        clapped = False
    else:
        clapped = True

    clap_count = post.claps.count()

    return JsonResponse({
        "clapped": clapped,
        "clap_count": clap_count
    })



@login_required
def create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        subtitle = request.POST.get('subtitle')
        featured_image = request.FILES.get('featured_image')
        
        
        if not title:
            messages.error(request, "Title is required.")
            return render(request, "blog/create.html")
        

        if not content:
            messages.error(request, "Content is required.")
            return render(request, "blog/create.html")

        try:
            content_data = json.loads(content)
        except json.JSONDecodeError:
            messages.error(request, "Invalid content format.")
            return render(request, "blog/create.html")
        

        post=Post.objects.create(
            title=title,
            content=content_data,
            subtitle=subtitle,
            featured_image = featured_image,
            author=request.user, 
            is_published = False
        )

        # messages.success(request, 'Post published successfully')
        return redirect('preview', id=post.id)

    return render(request, 'blog/create.html')


# -------------------------
# Update Post
# -------------------------
@login_required
def update(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)

    # # Ensure only author can edit (optional, Phase-7 improvement)
    # if post.author != request.user:
    #     # return HttpResponseForbidden()
    #     messages.error(request, 'You are not allowed to edit this post')
    #     return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        featured_image = request.FILES.get('featured_image')

        try:
            content_data = json.loads(content)
        except:
            messages.error(request, "Invalid content format.")
            return render(request, 'blog/update.html', {'post': post})

        post.title = title
        post.content = content_data

        if featured_image:
            post.featured_image = featured_image

        post.save()

        messages.success(request, 'Post updated successfully')

        return redirect('preview', id=post.id)
    return render(request, 'blog/update.html', {'post': post})



# -------------------------
# Delete Post
# -------------------------
@login_required
def delete(request, id):
    post = get_object_or_404(Post, id=id)

    # Optional: Only author can delete (Phase-7)
    if post.author != request.user:
        # return HttpResponseForbidden()
        messages.error(request, 'You are not allowed to delete this post')
        return redirect('home')
    
    post.delete()
    messages.success(request, 'Post deleted successfully')
    return redirect('home')





#  signup form view

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully')
            return redirect('home')
        
    else:
            form = SignupForm()
            
    return render(request, 'accounts/signup.html', {'form': form})    










@login_required
def complete_profile(request):
    profile = request.user.profile

    # if profile.is_completed:
    #     return redirect("home")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():

            # 🔥 Save User name
            # user = request.user
            # user.first_name = form.cleaned_data["first_name"]
            # user.last_name = form.cleaned_data["last_name"]
            # user.save()

            # Save profile
            profile = form.save(commit=False)
            profile.is_completed = True
            profile.save()

            return redirect("home")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/complete_profile.html", {"form": form})











@login_required
def upload_inline_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        image = request.FILES["image"]

        file_path = default_storage.save(
            f"posts/content/{image.name}",
            image
        )

        image_url = settings.MEDIA_URL + file_path

        return JsonResponse({
            "success": 1,
            "file": {
                "url": image_url
            }
        })

    return JsonResponse({"success": 0})









@login_required
def preview(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)
    return render(request, 'blog/preview.html', {'post': post})

@login_required
def publish_final(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)

    post.is_published = True
    post.save()

    messages.success(request, "Post published successfully.")
    return redirect('home')







@login_required
def schedule_post(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)

    if request.method == "POST":
        scheduled_time = request.POST.get("scheduled_time")

        if scheduled_time:
            scheduled_time = parse_datetime(scheduled_time)
            
            post.scheduled_at = scheduled_time
            
            post.is_published = False
            post.save()

            messages.success(request, "Post scheduled successfully.")
            # return redirect("stories")
            return redirect("stories")

    return redirect("preview", id=id)



@login_required
def cancel_schedule(request, id):

    post = get_object_or_404(Post, id=id, author=request.user)

    post.scheduled_at = None
    post.save()

    messages.success(request,"Schedule cancelled.")

    return redirect("preview", id=id)

 



@login_required
def profile_detail(request):

    user = request.user
    profile = user.profile

    posts = Post.objects.filter(
        author=user,
        is_published=True
    ).order_by("-created_at")

    post_count = posts.count()

    clap_count = Clap.objects.filter(
        post__author=user
    ).count()

    comment_count = Comment.objects.filter(
        post__author=user
    ).count()

    latest_post = posts.first()
    
    followers_count = Follow.objects.filter(
        following=user
    ).count()

    following_count = Follow.objects.filter(
        follower=user
    ).count()

    context = {
        "profile": profile,
        "post_count": post_count,
        "clap_count": clap_count,
        "comment_count": comment_count,
        "joined": user.date_joined,
        "latest_post": latest_post,
        "followers_count": followers_count,
        "following_count": following_count,
    }

    return render(request, "accounts/profile_detail.html", context)
    
    

    
    

    
# @login_required
# def stories(request):

#     user = request.user

#     published_posts = Post.objects.filter(
#         author=user,
#         is_published=True
#     ).order_by("-created_at")

#     drafts = Post.objects.filter(
#         author=user,
#         is_published=False
#         scheduled_for_isnull=True
#     ).order_by("-updated_at")

#     context = {
#         "published_posts": published_posts,
#         "drafts": drafts,
#         "published_count": published_posts.count(),
#         "draft_count": drafts.count(),
#     }

#     return render(request, "accounts/stories.html", context)    
    



@login_required
def stories(request):

    user = request.user

    drafts = Post.objects.filter(
        author=user,
        is_published=False,
        scheduled_at__isnull=True
    ).order_by("-updated_at")

    scheduled = Post.objects.filter(
        author=user,
        is_published=False,
        scheduled_at__isnull=False
    ).order_by("scheduled_at")

    published_posts = Post.objects.filter(
        author=user,
        is_published=True
    ).order_by("-created_at")

    context = {
        "drafts": drafts,
        "scheduled": scheduled,
        "published_posts": published_posts,

        "draft_count": drafts.count(),
        "scheduled_count": scheduled.count(),
        "published_count": published_posts.count(),
    }

    return render(request, "accounts/stories.html", context)




    
# @login_required
# def stats(request):

#     user = request.user

#     posts = Post.objects.filter(author=user)

#     post_count = posts.count()

#     clap_count = Clap.objects.filter(
#         post__author=user
#     ).count()

#     comment_count = Comment.objects.filter(
#         post__author=user
#     ).count()

#     return render(request, "accounts/stats.html", {
#         "post_count": post_count,
#         "clap_count": clap_count,
#         "comment_count": comment_count
#     })
    
    
    
from django.db.models import Count
from django.db.models.functions import TruncMonth

@login_required
def stats(request):

    user = request.user

    posts = Post.objects.filter(author=user)

    post_count = posts.count()

    clap_count = Clap.objects.filter(
        post__author=user
    ).count()
    comment_count = Comment.objects.filter(
        post__author=user
    ).count()

    # Top performing posts
    top_posts = Post.objects.filter(
        author=user,
        is_published=True
    ).annotate(
        clap_total=Count("claps"),
        comment_total=Count("comments")
    ).order_by("-clap_total")[:5]

    # Monthly post activity
    monthly_posts = Post.objects.filter(
        author=user
    ).annotate(
        month=TruncMonth("created_at")
    ).values("month").annotate(
        total=Count("id")
    ).order_by("month")

    labels = []
    data = []

    for item in monthly_posts:
        labels.append(item["month"].strftime("%b %Y"))
        data.append(item["total"])

    context = {
        "post_count": post_count,
        "clap_count": clap_count,
        "comment_count": comment_count,
        "top_posts": top_posts,
        "chart_labels": labels,
        "chart_data": data,
    }

    return render(request, "accounts/stats.html", context)    
    
# @login_required
# def library(request):

#     claps = Clap.objects.filter(user=request.user)

#     posts = [clap.post for clap in claps]

#     return render(request, "accounts/library.html", {
#         "posts": posts
#     })            
    
    
    
@login_required
def library(request):

    claps = Clap.objects.filter(user=request.user).select_related("post")

    posts = []
    seen = set()

    for clap in claps:
        if clap.post.id not in seen:
            posts.append(clap.post)
            seen.add(clap.post.id)

    return render(request, "accounts/library.html", {
        "posts": posts
    })    
    
 


def extract_text(content):
    try:
        data = json.loads(content)
        text = ""
        for block in data.get("blocks", []):
            text += block.get("data", {}).get("text", "") + " "
        return text.strip()
    except:
        return content 
 
    
    
    
def public_profile(request, id):
    user = get_object_or_404(User, id=id)
    profile = user.profile

    posts = Post.objects.filter(
        author=user,
        is_published=True
    ).order_by("-created_at")
    
    for post in posts:
        blocks = post.content.get("blocks", [])
        text_content = ""

        for block in blocks:
            if block["type"] == "paragraph":
                text_content += block["data"].get("text", "") + " "

            elif block["type"] == "header":
                text_content += block["data"].get("text", "") + " "

        post.preview = text_content.strip()

    # 🔥 NEW LOGIC
    is_following = False

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()

    followers_count = Follow.objects.filter(
        following=user
    ).count()
    
    
    following_count = Follow.objects.filter(
        follower=user
    ).count()

    context = {
        "author": user,
        "profile": profile,
        "posts": posts,
        "is_following":is_following,
        "followers_count":followers_count,
        "following_count": following_count,  
    }

    return render(request, "blog/public_profile.html", context)    





@login_required
# @require_POST
def toggle_follow(request, id):

    target_user = get_object_or_404(User, id=id)

    # ❌ Prevent self-follow
    if request.user == target_user:
        return JsonResponse({"error": "You cannot follow yourself"}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    if not created:
        follow.delete()
        following = False
    else:
        following = True

    followers_count = Follow.objects.filter(following=target_user).count()

    return JsonResponse({
        "following": following,
        "followers_count": followers_count
    })
    
    
    
    
    
# def followers_list(request, id):
#     user = get_object_or_404(User, id=id)

#     follows = Follow.objects.filter(following=user).select_related("follower")

#     users = [f.follower for f in follows]

#     return render(request, "blog/follow_list.html", {
#         "users": users,
#         "title": "Followers",
#         "profile_user": user
#     })


# def following_list(request, id):
#     user = get_object_or_404(User, id=id)

#     follows = Follow.objects.filter(follower=user).select_related("following")

#     users = [f.following for f in follows]

#     return render(request, "blog/follow_list.html", {
#         "users": users,
#         "title": "Following",
#         "profile_user": user
#     })    
    
    
    
def followers_list(request, id):
    user = get_object_or_404(User, id=id)

    follows = Follow.objects.filter(following=user).select_related("follower")

    users_data = []

    for f in follows:
        u = f.follower

        is_following = False
        if request.user.is_authenticated:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=u
            ).exists()

        users_data.append({
            "user": u,
            "is_following": is_following
        })

    return render(request, "blog/follow_list.html", {
        "users_data": users_data,
        "title": "Followers",
        "profile_user": user
    })


def following_list(request, id):
    user = get_object_or_404(User, id=id)

    follows = Follow.objects.filter(follower=user).select_related("following")

    users_data = []

    for f in follows:
        u = f.following

        is_following = False
        if request.user.is_authenticated:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=u     
                ).exists()

        users_data.append({
            "user": u,
            "is_following": is_following
        })

    return render(request, "blog/follow_list.html", {
        "users_data": users_data,
        "title": "Following",
        "profile_user": user
    })    
     