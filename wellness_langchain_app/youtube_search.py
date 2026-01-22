"""
YouTube search utility for finding workout and mindfulness videos
"""

from typing import Optional


def get_youtube_link(query: str, duration: str = "medium") -> Optional[str]:
    """
    Search for a YouTube video and return the first result's URL.
    
    Args:
        query: Search query string
        duration: Video duration filter (short, medium, long)
        
    Returns:
        YouTube video URL or None if no results found
    """
    try:
        # Try using youtube-search-python library
        from youtubesearchpython import VideosSearch
        
        # Perform search
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()
        
        # Extract video link
        if result and 'result' in result and len(result['result']) > 0:
            video_url = result['result'][0]['link']
            return video_url
        
        return None
        
    except ImportError:
        # If library not installed, try alternative method
        print("youtube-search-python not installed, trying alternative...")
        try:
            import urllib.parse
            import urllib.request
            import re
            
            # Search YouTube and extract first video ID
            query_string = urllib.parse.urlencode({"search_query": query})
            html = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"
            
            return None
            
        except Exception as e:
            print(f"Alternative YouTube search failed: {e}")
            return None
    
    except Exception as e:
        print(f"YouTube search error: {e}")
        # Try the alternative method as fallback
        try:
            import urllib.parse
            import urllib.request
            import re
            
            query_string = urllib.parse.urlencode({"search_query": query})
            html = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"
            
        except Exception as fallback_error:
            print(f"Fallback search also failed: {fallback_error}")
        
        return None


if __name__ == "__main__":
    # Test the function
    test_query = "beginner yoga 20 minutes"
    result = get_youtube_link(test_query)
    print(f"Search: {test_query}")
    print(f"Result: {result}")
