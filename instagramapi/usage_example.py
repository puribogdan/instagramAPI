#!/usr/bin/env python3
"""
Usage example for the numbered Instagram download functionality
"""

import sys
import os
sys.path.append('.')

from instaloader_setup import InstagramLoader

def main():
    """Example usage of the new numbered download functionality"""
    print("Instagram Numbered Download Example")
    print("=" * 40)

    # Initialize Instagram loader
    ig = InstagramLoader()

    # Set download directory (optional)
    download_dir = "instagram_numbered_downloads"
    ig.set_download_dir(download_dir)

    # Example Instagram URLs - replace with your actual URLs
    instagram_urls = [
        "https://www.instagram.com/p/YOUR_FIRST_POST/",
        "https://www.instagram.com/reel/YOUR_FIRST_REEL/",
        "https://www.instagram.com/p/YOUR_CAROUSEL_POST/"
    ]

    print(f"URLs to process: {len(instagram_urls)}")
    for i, url in enumerate(instagram_urls, 1):
        print(f"  {i}. {url}")

    print(f"\nFiles will be saved as:")
    print(f"  1profile.png, 1thumb.png, 1.jpg, 2.jpg, etc.")
    print(f"  2profile.png, 2thumb.png, 1.jpg, 2.jpg, etc.")
    print(f"  3profile.png, 3thumb.png, 1.jpg, 2.jpg, etc.")

    # Ask user if they want to proceed
    proceed = input("\nProceed with download? (y/N): ").strip().lower()
    if proceed == 'y':
        # Start downloading with numbered assets
        ig.download_post_with_numbered_assets(instagram_urls, start_number=1)

        print("\nDownload completed!")
        print(f"Files saved to: {download_dir}")

        # List downloaded files
        if os.path.exists(download_dir):
            files = os.listdir(download_dir)
            print(f"\nDownloaded {len(files)} files:")
            for file in sorted(files):
                print(f"  {file}")
    else:
        print("Download cancelled.")

if __name__ == "__main__":
    main()