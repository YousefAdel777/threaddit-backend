import logging
import requests
import os
import cv2
from nudenet import NudeDetector
from better_profanity import profanity
from celery import shared_task
from django.db.transaction import atomic
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from .models import Post
from .services import PostService
from .serializers import PostWriteSerializer
from communities.models import Community
User = get_user_model()

logger = logging.getLogger(__name__)

detector = NudeDetector()

def is_image_nsfw(image_path, threshold=0.5):
    result = detector.detect(image_path)
    for detection in result:
        if detection["score"] > threshold:
            return True
    return False

def extract_frames(video_path, output_dir, fps=1):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_count += 1
        frame_count += 1
    cap.release()
    return saved_count

def is_video_nsfw(video_path, output_dir="frames", fps=1, threshold=0.5):
    extract_frames(video_path, output_dir, fps)
    for frame_name in os.listdir(output_dir):
        frame_path = os.path.join(output_dir, frame_name)
        if is_image_nsfw(frame_path, threshold):
            return True
    return False

@shared_task
@atomic
def check_nsfw_post(post_id):
    post = Post.objects.filter(pk=post_id).first()
    if not post or not post.is_nsfw:
        return
    if post.content and profanity.contains_profanity(post.content):
        post.is_nsfw = True
        post.save(update_fields=['is_nsfw'])
        return
    if post.link and profanity.contains_profanity(post.link):
        post.is_nsfw = True
        post.save(update_fields=['is_nsfw'])
        return
    for attachment in post.attachments:
        is_nsfw = False
        if attachment.file_type == 'video':
            is_nsfw = is_video_nsfw(attachment.file.path)
        elif attachment.file_type == 'image':
            is_nsfw = is_image_nsfw(attachment.file.path)
        if is_nsfw:
            post.is_nsfw = True
            post.save(update_fields=['is_nsfw'])
            return

@shared_task
@atomic
def generate_posts():
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        logger.warning("No superuser found.")
        return
    try:
        response = requests.get(
            f"{settings.NEWS_API_URL}?access_key={settings.NEWS_API_KEY}&category=-general&languages=en",
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch: {e}")
        return
    data = response.json().get('data', [])
    for item in data:
        try:
            community = Community.objects.filter(
                topics__name=item['category'].capitalize(), 
                members__user=user, 
                members__is_moderator=True
            ).first()
            if not community:
                continue
            post_data = {
                'type': 'link',
                'user': user.id,
                'title': item.get('title'),
                'content': item.get('description'),
                'link': item.get('url'),
                'community': community.id,
            }
            serializer = PostWriteSerializer(data=post_data)
            serializer.is_valid(raise_exception=True)
            post = PostService.create_post(**serializer.validated_data)
            post.status = 'accepted'
            post.save(update_fields=['status'])
        except (ValueError, IntegrityError) as e:
            logger.error(f"Error creating post: {e}")
            continue
