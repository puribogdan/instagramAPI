#!/usr/bin/env python3
"""
Instagram automation script using Instaloader API
"""

import instaloader
from instaloader import Instaloader, Profile
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Instagram credentials from .env file
def get_instagram_credentials() -> tuple[str, str]:
    """Get Instagram credentials from .env file"""
    username = os.getenv('INSTA_USERNAME')
    password = os.getenv('INSTA_PASSWORD')

    if not username or not password:
        raise ValueError("Instagram credentials not found in .env file. Please ensure INSTA_USERNAME and INSTA_PASSWORD are set.")

    return username, password

IG_USERNAME, IG_PASSWORD = get_instagram_credentials()


class InstagramLoader:
    def __init__(self, username=None, password=None, download_dir=None):
        """Initialize Instaloader instance"""
        self.loader = Instaloader()
        self.username = username or IG_USERNAME
        self.password = password or IG_PASSWORD

        # Configure Instaloader to save files in a flat structure without subdirectories
        self.loader.dirname_pattern = ""  # Disable subdirectory creation
        self.loader.filename_pattern = "{shortcode}"
        self.loader.save_metadata = False  # Disable metadata files
        self.loader.post_metadata_txt_pattern = ""  # Disable post metadata text files

        # Set download directory (user-specified or default)
        self.download_dir = download_dir or "instagram_downloads"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Login with credentials
        self.login()

        # Clean up any existing .txt files in download directory
        self._cleanup_txt_files()

    def login(self):
        """Login to Instagram using Instaloader"""
        try:
            self.loader.login(self.username, self.password)
            return True
        except instaloader.exceptions.BadCredentialsException:
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            return False
        except instaloader.exceptions.LoginException:
            return False
        except Exception:
            return False

    def check_login_status(self):
        """Check if currently logged in"""
        try:
            # Try to access a public profile to verify login is working
            Profile.from_username(self.loader.context, "instagram")
            return True
        except Exception as e:
            print(f"Login check failed: {e}")
            return False

    def _cleanup_txt_files(self):
        """Remove any existing .txt files from download directory"""
        if os.path.exists(self.download_dir):
            for filename in os.listdir(self.download_dir):
                if filename.endswith('.txt'):
                    txt_file_path = os.path.join(self.download_dir, filename)
                    try:
                        os.remove(txt_file_path)
                    except Exception:
                        pass  # Silently handle cleanup errors

    def _download_carousel_post(self, post):
        """Download carousel post and rename files as 1, 2, 3, etc."""
        try:
            # Download to the specified directory with flat structure
            old_dirname_pattern = self.loader.dirname_pattern
            old_filename_pattern = self.loader.filename_pattern

            # Temporarily set patterns to ensure flat structure in the target directory
            self.loader.dirname_pattern = self.download_dir
            self.loader.filename_pattern = "{shortcode}"

            self.loader.download_post(post, target=self.download_dir)

            # Restore original patterns
            self.loader.dirname_pattern = old_dirname_pattern
            self.loader.filename_pattern = old_filename_pattern

        except Exception as e:
            print(f"Error downloading carousel post: {e}")


    def set_download_dir(self, new_dir):
        """Set new download directory and clean up any .txt files"""
        self.download_dir = new_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)
        self._cleanup_txt_files()

    def get_profile_info(self, target_username):
        """Get profile information for a specific user"""
        try:
            profile = Profile.from_username(self.loader.context, target_username)
            # Handle Unicode characters safely in print statements
            try:
                print(f"Profile: {self._safe_print(profile.username)}")
                print(f"Full Name: {self._safe_print(profile.full_name)}")
                print(f"Bio: {self._safe_print(profile.biography)}")
            except UnicodeEncodeError:
                print(f"Profile: {self._safe_print(target_username)}")
                print("Full Name: [Unicode content]")
                print("Bio: [Unicode content]")

            print(f"Followers: {profile.followers}")
            print(f"Following: {profile.followees}")
            print(f"Posts: {profile.mediacount}")
            print(f"Is Private: {profile.is_private}")
            print(f"Is Verified: {profile.is_verified}")
            return profile
        except Exception as e:
            print(f"Error getting profile info: {e}")
            return None

    def download_profile_posts(self, target_username, max_posts=10):
        """Download recent posts from a profile"""
        try:
            profile = Profile.from_username(self.loader.context, target_username)
            print(f"Downloading up to {max_posts} posts from {target_username}...")
            post_count = 0

            # Temporarily set patterns to ensure flat structure in the target directory
            old_dirname_pattern = self.loader.dirname_pattern
            old_filename_pattern = self.loader.filename_pattern
            self.loader.dirname_pattern = self.download_dir
            self.loader.filename_pattern = "{shortcode}"

            for post in profile.get_posts():
                if post_count >= max_posts:
                    break

                # Check if this is a carousel post
                sidecar_nodes = list(post.get_sidecar_nodes())
                is_carousel = len(sidecar_nodes) > 0
    
                if is_carousel:
                    self._download_carousel_post(post)
                else:
                    self.loader.download_post(post, target=self.download_dir)
                post_count += 1

            # Restore original patterns
            self.loader.dirname_pattern = old_dirname_pattern
            self.loader.filename_pattern = old_filename_pattern

            print(f"Downloaded {post_count} posts to {self.download_dir}")
        except Exception as e:
            print(f"Error downloading posts: {e}")

    def download_post_by_shortcode(self, shortcode):
        """Download a specific post by its shortcode"""
        try:
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            # Check if this is a carousel post
            sidecar_nodes = list(post.get_sidecar_nodes())
            is_carousel = len(sidecar_nodes) > 0

            if is_carousel:
                self._download_carousel_post(post)
            else:
                # Download to the specified directory with flat structure
                old_dirname_pattern = self.loader.dirname_pattern
                old_filename_pattern = self.loader.filename_pattern

                # Temporarily set patterns to ensure flat structure in the target directory
                self.loader.dirname_pattern = self.download_dir
                self.loader.filename_pattern = "{shortcode}"

                self.loader.download_post(post, target=self.download_dir)

                # Restore original patterns
                self.loader.dirname_pattern = old_dirname_pattern
                self.loader.filename_pattern = old_filename_pattern

        except Exception as e:
            print(f"Error downloading post: {e}")

    def search_hashtag(self, hashtag, max_posts=5):
        """Search for posts with a specific hashtag"""
        try:
            posts = self.loader.get_hashtag_posts(hashtag)
            print(f"Searching for hashtag: #{hashtag}")
            post_count = 0
            for post in posts:
                if post_count >= max_posts:
                    break
                print(f"Post by {post.owner_username}: {post.shortcode}")
                print(f"Caption: {post.caption[:100] if post.caption else 'No caption'}...")
                print(f"Likes: {post.likes}")
                print("---")
                post_count += 1
            print(f"Found {post_count} posts for #{hashtag}")
        except Exception as e:
            print(f"Error searching hashtag: {e}")

    def download_reels_from_urls(self, reel_urls):
        """Download Instagram reels from a list of URLs"""
        print(f"Downloading {len(reel_urls)} reels...")
        for i, url in enumerate(reel_urls, 1):
            try:
                if '/reel/' in url:
                    shortcode = url.split('/reel/')[1].split('/')[0].split('?')[0]
                else:
                    continue

                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

                # Check if this is a carousel post
                sidecar_nodes = list(post.get_sidecar_nodes())
                is_carousel = len(sidecar_nodes) > 0

                if is_carousel:
                    # Temporarily set patterns for carousel download
                    old_dirname_pattern = self.loader.dirname_pattern
                    old_filename_pattern = self.loader.filename_pattern
                    self.loader.dirname_pattern = self.download_dir
                    self.loader.filename_pattern = "{shortcode}"

                    self._download_carousel_post(post)

                    # Restore original patterns
                    self.loader.dirname_pattern = old_dirname_pattern
                    self.loader.filename_pattern = old_filename_pattern
                else:
                    # Temporarily set patterns to ensure flat structure in the target directory
                    old_dirname_pattern = self.loader.dirname_pattern
                    old_filename_pattern = self.loader.filename_pattern
                    self.loader.dirname_pattern = self.download_dir
                    self.loader.filename_pattern = "{shortcode}"

                    self.loader.download_post(post, target=self.download_dir)

                    # Restore original patterns
                    self.loader.dirname_pattern = old_dirname_pattern
                    self.loader.filename_pattern = old_filename_pattern


            except Exception as e:
                pass  # Silently handle download errors

    def extract_profile_info_from_reel(self, reel_url):
        """Extract profile information from a reel URL"""
        try:
            if '/reel/' in reel_url:
                shortcode = reel_url.split('/reel/')[1].split('/')[0].split('?')[0]
            else:
                print(f"Invalid post URL format: {reel_url}")
                return None

            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            profile_info = {
                'username': post.owner_username,
                'full_name': getattr(post.owner_profile, 'full_name', ''),
                'bio': getattr(post.owner_profile, 'biography', ''),
                'followers': getattr(post.owner_profile, 'followers', 0),
                'following': getattr(post.owner_profile, 'followees', 0),
                'is_private': getattr(post.owner_profile, 'is_private', False),
                'is_verified': getattr(post.owner_profile, 'is_verified', False),
                'profile_pic_url': getattr(post.owner_profile, 'profile_pic_url', ''),
                'reel_caption': post.caption if post.caption else '',
                'reel_shortcode': post.shortcode,
                'likes': getattr(post, 'likes', 0)
            }
            return profile_info
        except Exception as e:
            print(f"Error extracting profile info: {e}")
            return None

    def extract_shortcode_from_url(self, url):
        """Extract shortcode from Instagram URL"""
        try:
            if '/reel/' in url:
                return url.split('/reel/')[1].split('/')[0].split('?')[0]
            elif '/p/' in url:
                return url.split('/p/')[1].split('/')[0].split('?')[0]
            else:
                print(f"Invalid Instagram URL format: {url}")
                return None
        except Exception as e:
            print(f"Error extracting shortcode: {e}")
            return None

    def extract_profile_info_from_url(self, url):
        """Extract profile information from any Instagram post/reel URL"""
        try:
            shortcode = self.extract_shortcode_from_url(url)
            if not shortcode:
                return None

            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            profile_info = {
                'username': post.owner_username,
                'full_name': self._safe_print(getattr(post.owner_profile, 'full_name', '')),
                'bio': self._safe_print(getattr(post.owner_profile, 'biography', '')),
                'followers': getattr(post.owner_profile, 'followers', 0),
                'following': getattr(post.owner_profile, 'followees', 0),
                'is_private': getattr(post.owner_profile, 'is_private', False),
                'is_verified': getattr(post.owner_profile, 'is_verified', False),
                'profile_pic_url': getattr(post.owner_profile, 'profile_pic_url', ''),
                'caption': self._safe_print(post.caption if post.caption else ''),
                'shortcode': post.shortcode,
                'likes': getattr(post, 'likes', 0),
                'post_type': 'reel' if '/reel/' in url else 'post'
            }
            return profile_info
        except Exception as e:
            print(f"Error extracting profile info: {e}")
            return None

    def download_post_with_numbered_assets(self, urls, start_number=1):
        """Download posts with specific naming convention: 1profile.png, 1thumb.png, etc."""
        print(f"Downloading {len(urls)} posts with numbered assets starting from {start_number}...")

        for i, url in enumerate(urls, start_number):
            try:
                print(f"\nProcessing URL {i}: {url}")

                # Extract shortcode and post info
                shortcode = self.extract_shortcode_from_url(url)
                if not shortcode:
                    print(f"Could not extract shortcode from URL: {url}")
                    continue

                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                profile_info = self.extract_profile_info_from_url(url)

                if not profile_info:
                    print(f"Could not extract profile info for URL: {url}")
                    continue

                # Print requested information in specified format
                print(f"\nVideo description: {self._safe_print(profile_info.get('caption', 'No caption'))}")
                print(f"Profile URL: https://www.instagram.com/{profile_info['username']}/")
                print(f"Nickname: @{profile_info['username']}")
                print(f"Fullname: {self._safe_print(profile_info.get('full_name', 'N/A'))}")

                print(f"Post by: {profile_info['username']}")
                # Handle Unicode characters in caption safely
                try:
                    caption = profile_info.get('caption', 'No caption')[:50] if profile_info.get('caption') else 'No caption'
                    print(f"Caption: {self._safe_print(caption)}...")
                except UnicodeEncodeError:
                    print(f"Caption: [Content unavailable due to encoding]...")

                # Download profile image
                profile = None
                try:
                    print(f"[DEBUG] Attempting to access profile for username: {self._safe_print(profile_info['username'])}")
                    profile = instaloader.Profile.from_username(self.loader.context, profile_info['username'])
                    print(f"[DEBUG] Successfully accessed profile: {self._safe_print(profile.username)}")
                    self._download_profile_image(profile, i)
                except Exception as e:
                    print(f"[DEBUG] Could not access profile for {self._safe_print(profile_info['username'])}: {e}")
                    print(f"[DEBUG] Profile info available: {profile_info.get('profile_pic_url', 'No URL')}")
                    # Try with the URL from profile_info as fallback
                    if profile_info.get('profile_pic_url'):
                        print(f"[DEBUG] Using fallback method with profile_pic_url")
                        self._download_profile_image_fallback(profile_info['profile_pic_url'], i)
                    else:
                        print(f"[DEBUG] No profile_pic_url available for fallback")

                # Download thumbnail
                self._download_thumbnail(post, i)

                # Download post assets
                self._download_post_assets(post, i)

                print(f"Completed download for URL {i}")

            except Exception as e:
                print(f"Error processing URL {i}: {e}")
                continue

    def _download_profile_image(self, profile, number):
        """Download profile image as {number}profile.png"""
        try:
            print(f"[DEBUG] Starting profile image download for {number}profile.png")

            # Get profile picture URL from profile object
            profile_pic_url = getattr(profile, 'profile_pic_url', None)

            if not profile_pic_url:
                print(f"[DEBUG] No profile picture URL found")
                print(f"[DEBUG] Available profile attributes: {[attr for attr in dir(profile) if 'pic' in attr.lower()]}")
                return

            print(f"[DEBUG] Found profile picture URL: {profile_pic_url}")

            print(f"[DEBUG] Downloading profile image from: {profile_pic_url}")

            response = requests.get(profile_pic_url, stream=True, timeout=10)
            print(f"[DEBUG] HTTP response status: {response.status_code}")

            if response.status_code == 200:
                profile_filename = f"{number}profile.png"
                profile_path = os.path.join(self.download_dir, profile_filename)
                print(f"[DEBUG] Saving to: {profile_path}")

                with open(profile_path, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(profile_path)
                print(f"[DEBUG] Downloaded profile image: {profile_filename} ({file_size} bytes)")
            else:
                print(f"[DEBUG] Failed to download profile image for {number}profile.png (HTTP {response.status_code})")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")

        except Exception as e:
            print(f"[DEBUG] Error downloading profile image {number}profile.png: {e}")
            import traceback
            traceback.print_exc()

    def _download_profile_image_fallback(self, profile_pic_url, number):
        """Fallback method to download profile image using URL directly"""
        try:
            if not profile_pic_url:
                print(f"[DEBUG] No profile picture URL available for fallback {number}profile.png")
                return

            print(f"[DEBUG] Using fallback method for profile image: {profile_pic_url}")

            # Ensure the URL is properly formatted
            if not profile_pic_url.startswith('http'):
                print(f"[DEBUG] Invalid URL format: {profile_pic_url}")
                return

            response = requests.get(profile_pic_url, stream=True, timeout=10)
            print(f"[DEBUG] Fallback HTTP response status: {response.status_code}")

            if response.status_code == 200:
                profile_filename = f"{number}profile.png"
                profile_path = os.path.join(self.download_dir, profile_filename)
                print(f"[DEBUG] Saving fallback profile image to: {profile_path}")

                with open(profile_path, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(profile_path)
                print(f"[DEBUG] Downloaded profile image (fallback): {profile_filename} ({file_size} bytes)")
            else:
                print(f"[DEBUG] Failed to download profile image (fallback) for {number}profile.png (HTTP {response.status_code})")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")

        except Exception as e:
            print(f"[DEBUG] Error downloading profile image (fallback) {number}profile.png: {e}")
            import traceback
            traceback.print_exc()

    def _download_thumbnail(self, post, number):
        """Download post thumbnail as {number}thumb.png"""
        try:
            thumb_url = None

            # Try multiple possible thumbnail URL attributes
            possible_attrs = ['display_url', 'url', 'thumbnail_url', 'thumb_url']

            for attr in possible_attrs:
                thumb_url = getattr(post, attr, None)
                if thumb_url:
                    break

            # For video posts, try to get video thumbnail
            if not thumb_url and hasattr(post, 'video_url'):
                # Try to construct thumbnail URL from video URL
                video_url = getattr(post, 'video_url', '')
                if video_url:
                    # Replace video URL patterns to get thumbnail
                    thumb_url = video_url.replace('/vid/', '/img/')

            if thumb_url:
                print(f"Downloading thumbnail from: {thumb_url}")

                response = requests.get(thumb_url, stream=True)
                if response.status_code == 200:
                    thumb_filename = f"{number}thumb.png"
                    thumb_path = os.path.join(self.download_dir, thumb_filename)

                    with open(thumb_path, 'wb') as f:
                        f.write(response.content)

                    print(f"Downloaded thumbnail: {thumb_filename}")
                else:
                    print(f"Failed to download thumbnail for {number}thumb.png (HTTP {response.status_code})")
            else:
                print(f"No thumbnail URL available for {number}thumb.png")
                print(f"Available post attributes: {[attr for attr in dir(post) if not attr.startswith('_')]}")

        except Exception as e:
            print(f"Error downloading thumbnail {number}thumb.png: {e}")

    def _download_post_assets(self, post, number):
        """Download post assets with proper numbering for carousel posts"""
        try:
            # Check if this is a carousel post - fix the generator issue
            sidecar_nodes = list(post.get_sidecar_nodes())  # Convert generator to list
            is_carousel = len(sidecar_nodes) > 0

            print(f"[DEBUG] Processing post {number} - Carousel: {is_carousel}, Nodes: {len(sidecar_nodes)}")
    
            # Skip location-related debugging to avoid API errors
            # post_attrs = [attr for attr in dir(post) if not attr.startswith('_') and hasattr(post, attr)]
            # url_attrs = [attr for attr in post_attrs if 'url' in attr.lower()]
            # print(f"[DEBUG] Available URL attributes on post: {url_attrs}")

            if is_carousel:
                # Handle carousel posts
                print(f"[DEBUG] Carousel post with {len(sidecar_nodes)} assets")

                for idx, node in enumerate(sidecar_nodes, 1):
                    print(f"[DEBUG] Processing carousel asset {idx}")

                    # Log available attributes on the node
                    node_attrs = [attr for attr in dir(node) if not attr.startswith('_') and hasattr(node, attr)]
                    node_url_attrs = [attr for attr in node_attrs if 'url' in attr.lower()]
                    print(f"[DEBUG] Available URL attributes on node {idx}: {node_url_attrs}")

                    # Check multiple possible URL attributes
                    asset_url = None
                    for attr in ['video_url', 'display_url', 'url']:
                        potential_url = getattr(node, attr, None)
                        if potential_url:
                            asset_url = potential_url
                            print(f"[DEBUG] Found URL for carousel asset {idx} via {attr}: {asset_url}")
                            break

                    if asset_url:
                        self._download_asset(asset_url, number, idx)
                    else:
                        print(f"[DEBUG] No URL found for carousel asset {idx}")
                        print(f"[DEBUG] Available node attributes: {node_attrs}")
            else:
                # Handle single post
                print(f"[DEBUG] Processing single post")

                # Check multiple possible URL attributes in order of preference
                asset_url = None
                for attr in ['video_url', 'display_url', 'url']:
                    potential_url = getattr(post, attr, None)
                    if potential_url:
                        asset_url = potential_url
                        print(f"[DEBUG] Found URL for single post via {attr}: {asset_url}")
                        break

                if asset_url:
                    self._download_asset(asset_url, number, 1)
                else:
                    print(f"[DEBUG] No asset URL found for single post")
                    # Removed post_attrs reference to avoid location API trigger

        except Exception as e:
            print(f"[DEBUG] Error downloading post assets for {number}: {e}")
            import traceback
            traceback.print_exc()

    def _download_asset(self, asset_url, number, asset_index):
        """Download a single asset with proper filename"""
        try:
            if not asset_url:
                print(f"[DEBUG] No asset URL provided for asset {asset_index} in post {number}")
                return

            print(f"[DEBUG] Downloading asset {asset_index} from: {asset_url}")

            response = requests.get(asset_url, stream=True)
            if response.status_code == 200:
                # Get content type from response headers
                content_type = response.headers.get('content-type', '').lower()
                print(f"[DEBUG] Content-Type: {content_type}")

                # Determine if this is a video based on content type or URL patterns
                is_video = False
                if 'video' in content_type:
                    is_video = True
                    print(f"[DEBUG] Detected video content type: {content_type}")
                elif 'mp4' in asset_url.lower() or 'webm' in asset_url.lower():
                    is_video = True
                    print(f"[DEBUG] Detected video URL pattern: {asset_url}")
                else:
                    print(f"[DEBUG] Assuming image content (Content-Type: {content_type})")

                # Determine file extension based on content type and URL
                if is_video:
                    if 'mp4' in content_type:
                        extension = '.mp4'
                    elif 'webm' in content_type:
                        extension = '.webm'
                    elif 'quicktime' in content_type or 'mov' in content_type:
                        extension = '.mov'
                    else:
                        # Fallback: check URL for video patterns
                        if 'mp4' in asset_url.lower():
                            extension = '.mp4'
                        elif 'webm' in asset_url.lower():
                            extension = '.webm'
                        elif 'mov' in asset_url.lower():
                            extension = '.mov'
                        else:
                            extension = '.mp4'  # Default to mp4 for videos
                    print(f"[DEBUG] Using video extension: {extension}")
                else:
                    # Handle image content
                    parsed_url = urlparse(asset_url)
                    url_path = parsed_url.path

                    # Extract extension from URL or default to jpg
                    if '.' in url_path:
                        extension = os.path.splitext(url_path)[1]
                        if not extension.startswith('.'):
                            extension = '.' + extension
                        # Handle URL-encoded extensions
                        extension = extension.lower()
                    else:
                        extension = '.jpg'

                    # Ensure we have a proper image extension
                    if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        extension = '.jpg'
                    print(f"[DEBUG] Using image extension: {extension}")

                # For carousel posts and single posts, include post number to avoid overwrites
                asset_filename = f"{number}-{asset_index}{extension}"
                asset_path = os.path.join(self.download_dir, asset_filename)
                print(f"[DEBUG] Saving asset to: {asset_path}")

                with open(asset_path, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(asset_path)
                print(f"[DEBUG] Downloaded asset: {asset_filename} ({file_size} bytes)")

            else:
                print(f"[DEBUG] Failed to download asset {asset_index} for post {number} (HTTP {response.status_code})")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")

        except Exception as e:
            print(f"[DEBUG] Error downloading asset {asset_index} for post {number}: {e}")
            import traceback
            traceback.print_exc()

    def _safe_print(self, text):
        """Safely print text handling Unicode encoding issues"""
        try:
            return str(text)
        except UnicodeEncodeError:
            return "[Unicode content]"


def get_user_input(prompt):
    """Get input from user"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        return None


def get_download_folder_from_user():
    """Get download folder path from user input"""
    print("\nEnter download folder path:")
    folder_path = get_user_input("Enter the full path to download folder (or press Enter for default 'instagram_downloads'): ")

    if folder_path is None:
        return None

    if not folder_path:
        folder_path = "instagram_downloads"

    # Expand user home directory if needed
    folder_path = os.path.expanduser(folder_path)

    return folder_path


def main():
    """Main interactive function with user-specified download folder"""
    print("Instagram Downloader - All files in same folder")
    print("=" * 50)

    # Get download folder from user
    download_folder = get_download_folder_from_user()
    if download_folder is None:
        return

    print(f"Download folder set to: {download_folder}")

    # Create loader with user-specified folder
    ig = InstagramLoader(download_dir=download_folder)

    print("\nEnter Instagram URLs:")
    urls_input = get_user_input("Enter the URLs (separate multiple URLs with spaces): ")
    if urls_input is None:
        return

    urls = [url.strip() for url in urls_input.split() if url.strip()]
    if not urls:
        print("No valid URLs provided")
        return

    print(f"\nDownloading to: {ig.download_dir}")
    print("Files will be saved as:")
    print("  - {number}profile.png (Profile pictures)")
    print("  - {number}thumb.png (Post thumbnails)")
    print("  - {number}-{asset}.ext (Post assets: 1-1.jpg, 1-2.jpg for post 1)")
    print("-" * 50)

    # Use the new method that downloads everything to the same folder
    ig.download_post_with_numbered_assets(urls, start_number=1)

    print(f"\nAll files downloaded to: {ig.download_dir}")
    print("Check the folder for: profile images, thumbnails, and post assets")



if __name__ == "__main__":
    main()
