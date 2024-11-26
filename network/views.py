from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import *


def index(request):
    all_posts = Post.objects.filter(creater__is_superuser=False).order_by('-date_created')
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    if page_number == None:
        page_number = 1
    posts = paginator.get_page(page_number)
    followings = []
    suggestions = []
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .exclude(is_superuser=True)\
                                .order_by("?")[:6]
    return render(request, "network/index.html", {
        "posts": posts,
        "suggestions": suggestions,
        "page": "all_posts",
        'profile': False
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        fname = request.POST["firstname"]
        lname = request.POST["lastname"]
        profile = request.FILES.get("profile")
        print(f"--------------------------Profile: {profile}----------------------------")
        cover = request.FILES.get('cover')
        print(f"--------------------------Cover: {cover}----------------------------")

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = fname
            user.last_name = lname
            if profile is not None:
                user.profile_pic = profile
            else:
                user.profile_pic = "profile_pic/no_pic.png"
            user.cover = cover           
            user.save()
            Follower.objects.create(user=user)
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")



def profile(request, username):
    user = User.objects.get(username=username)
    if user.is_superuser:
        return HttpResponseRedirect(reverse('index'))
        
    all_posts = Post.objects.filter(creater=user).order_by('-date_created')
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    if page_number == None:
        page_number = 1
    posts = paginator.get_page(page_number)
    followings = []
    suggestions = []
    follower = False
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .exclude(is_superuser=True)\
                                .order_by("?")[:6]

        if request.user in Follower.objects.get(user=user).followers.all():
            follower = True
    
    follower_count = Follower.objects.get(user=user).followers.all().count()
    following_count = Follower.objects.filter(followers=user).count()
    return render(request, 'network/profile.html', {
        "username": user,
        "posts": posts,
        "posts_count": all_posts.count(),
        "suggestions": suggestions,
        "page": "profile",
        "is_follower": follower,
        "follower_count": follower_count,
        "following_count": following_count
    })

def following(request):
    if request.user.is_authenticated:
        following_user = Follower.objects.filter(followers=request.user).values('user')
        all_posts = Post.objects.filter(creater__in=following_user)\
                              .filter(creater__is_superuser=False)\
                              .order_by('-date_created')
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page')
        if page_number == None:
            page_number = 1
        posts = paginator.get_page(page_number)
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .exclude(is_superuser=True)\
                                .order_by("?")[:6]
        return render(request, "network/index.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "following"
        })
    else:
        return HttpResponseRedirect(reverse('login'))

def saved(request):
    if request.user.is_authenticated:
        all_posts = Post.objects.filter(savers=request.user)\
                              .filter(creater__is_superuser=False)\
                              .order_by('-date_created')

        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page')
        if page_number == None:
            page_number = 1
        posts = paginator.get_page(page_number)

        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .exclude(is_superuser=True)\
                                .order_by("?")[:6]
        return render(request, "network/index.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "saved"
        })
    else:
        return HttpResponseRedirect(reverse('login'))
        


@login_required
def create_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        try:
            post = Post.objects.create(creater=request.user, content_text=text, content_image=pic)
            return HttpResponseRedirect(reverse('index'))
        except Exception as e:
            return HttpResponse(e)
    else:
        return HttpResponse("Method must be 'POST'")

@login_required
@csrf_exempt
def edit_post(request, post_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        img_chg = request.POST.get('img_change')
        post_id = request.POST.get('id')
        post = Post.objects.get(id=post_id)
        try:
            post.content_text = text
            if img_chg != 'false':
                post.content_image = pic
            post.save()
            
            if(post.content_text):
                post_text = post.content_text
            else:
                post_text = False
            if(post.content_image):
                post_image = post.img_url()
            else:
                post_image = False
            
            return JsonResponse({
                "success": True,
                "text": post_text,
                "picture": post_image
            })
        except Exception as e:
            print('-----------------------------------------------')
            print(e)
            print('-----------------------------------------------')
            return JsonResponse({
                "success": False
            })
    else:
            return HttpResponse("Method must be 'POST'")

@csrf_exempt
def like_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unlike_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def save_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unsave_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def follow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Follower: {request.user}......................")
            try:
                (follower, create) = Follower.objects.get_or_create(user=user)
                follower.followers.add(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unfollow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Unfollower: {request.user}......................")
            try:
                follower = Follower.objects.get(user=user)
                follower.followers.remove(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def comment(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            data = json.loads(request.body)
            comment = data.get('comment_text')
            post = Post.objects.get(id=post_id)
            try:
                newcomment = Comment.objects.create(post=post,commenter=request.user,comment_content=comment)
                post.comment_count += 1
                post.save()
                print(newcomment.serialize())
                return JsonResponse([newcomment.serialize()], safe=False, status=201)
            except Exception as e:
                return HttpResponse(e)
    
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post)
        comments = comments.order_by('-comment_time').all()
        return JsonResponse([comment.serialize() for comment in comments], safe=False)
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def delete_post(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(id=post_id)
            if request.user == post.creater:
                try:
                    delet = post.delete()
                    return HttpResponse(status=201)
                except Exception as e:
                    return HttpResponse(e)
            else:
                return HttpResponse(status=404)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

def load_more_suggestions(request):
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        # Get the next 6 suggestions, skipping the ones already shown
        current_count = int(request.GET.get('offset', 6))
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .exclude(is_superuser=True)\
                                .order_by("?")[current_count:current_count+6]
        
        return JsonResponse([{
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_pic': user.profile_pic.url if user.profile_pic else None
        } for user in suggestions], safe=False)
    return JsonResponse({'error': 'Login required'}, status=401)

def search(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        if query:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).exclude(username=request.user.username)\
             .exclude(is_superuser=True)\
             [:10]
            
            return JsonResponse([{
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_pic': user.profile_pic.url if user.profile_pic else None
            } for user in users], safe=False)
    
    return JsonResponse([], safe=False)

@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        try:
            # Update basic info
            user.first_name = request.POST.get('firstname', user.first_name)
            user.last_name = request.POST.get('lastname', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.bio = request.POST.get('bio', '')
            
            # Handle profile picture upload
            if 'profile_pic' in request.FILES:
                user.profile_pic = request.FILES['profile_pic']
                
            # Handle cover photo upload
            if 'cover' in request.FILES:
                user.cover = request.FILES['cover']
                
            user.save()
            return HttpResponseRedirect(reverse('profile', kwargs={'username': user.username}))
        except Exception as e:
            print(f"Error updating profile: {e}")
            return render(request, "network/edit_profile.html", {
                "message": "Error updating profile",
                "error": True
            })
    
    # GET request - show the edit form
    return render(request, "network/edit_profile.html", {
        "user": request.user
    })

@login_required
def chat_view(request):
    # Get all users that have chatted with current user, excluding admins
    chat_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | 
        Q(received_messages__sender=request.user)
    ).exclude(is_superuser=True).distinct()
    
    # Add unread message count and last message for each user
    formatted_users = []
    for user in chat_users:
        # Get unread count
        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()
        
        # Get the last message
        last_message = Message.objects.filter(
            Q(sender=user, receiver=request.user) |
            Q(sender=request.user, receiver=user)
        ).order_by('-timestamp').first()
        
        formatted_user = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_pic': user.profile_pic,
            'unread_count': unread_count
        }
        
        if last_message:
            formatted_user['last_message'] = last_message.content
            formatted_user['last_message_time'] = last_message.timestamp
        
        formatted_users.append(formatted_user)
    
    # Sort users by last message time
    formatted_users.sort(
        key=lambda x: x.get('last_message_time', user.date_joined),
        reverse=True
    )
    
    return render(request, "network/chat.html", {
        "chat_users": formatted_users,
        "page": "chat"
    })

@login_required
def chat_room(request, username):
    try:
        selected_user = User.objects.get(username=username)
        # Prevent accessing admin chats
        if selected_user.is_superuser:
            return HttpResponseRedirect(reverse('chat'))
    except User.DoesNotExist:
        return HttpResponseRedirect(reverse('chat'))
    
    # Get all users that have chatted with current user, excluding admins
    chat_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | 
        Q(received_messages__sender=request.user)
    ).exclude(is_superuser=True).distinct()
    
    # Format users same as in chat_view
    formatted_users = []
    for user in chat_users:
        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()
        
        last_message = Message.objects.filter(
            Q(sender=user, receiver=request.user) |
            Q(sender=request.user, receiver=user)
        ).order_by('-timestamp').first()
        
        formatted_user = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_pic': user.profile_pic,
            'unread_count': unread_count
        }
        
        if last_message:
            formatted_user['last_message'] = last_message.content
            formatted_user['last_message_time'] = last_message.timestamp
        
        formatted_users.append(formatted_user)
    
    # Sort users by last message time
    formatted_users.sort(
        key=lambda x: x.get('last_message_time', user.date_joined),
        reverse=True
    )
    
    return render(request, "network/chat.html", {
        "chat_users": formatted_users,
        "selected_user": selected_user,
        "page": "chat"
    })

@login_required
def get_messages(request, username):
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    messages = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) |
         Q(sender=other_user, receiver=request.user))
    ).order_by('timestamp')
    
    # Mark messages as read
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse([message.serialize() for message in messages], safe=False)

@login_required
@csrf_exempt
def send_message(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required"}, status=400)
    
    data = json.loads(request.body)
    receiver_username = data.get("receiver")
    content = data.get("content")
    
    try:
        receiver = User.objects.get(username=receiver_username)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content
    )
    
    return JsonResponse({"success": True, "message": message.serialize()})

@login_required
def get_unread_count(request, username):
    try:
        other_user = User.objects.get(username=username)
        count = Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).count()
        return JsonResponse({"count": count})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

@login_required
def get_total_unread(request):
    total_unread = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    return JsonResponse({"count": total_unread})
