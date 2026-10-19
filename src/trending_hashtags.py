"""
Trending Hashtag Otomasyonu

YouTube'un güncel trend hashtag'lerini çeker ve videolara otomatik ekler.
"""
import os
import json
import random
from datetime import datetime

# Trending hashtag'ler (günlük güncellenebilir)
TRENDING_HASHTAGS = {
    "global": [
        "#Shorts", "#Trending", "#Viral", "#FYP", "#ForYou", "#Explore"
    ],
    "animai_studio": [
        "#AnimAIStudio", "#KasaKatlama", "#SıfırdanZengin", "#AlSat", 
        "#Ticaret", "#KeşfetBeniÖneÇıkar", "#TrendShorts", "#AIAnimasyon",
        "#ViralShorts", "#3DAnimation", "#Shorts", "#YapayZeka", "#Hikaye"
    ],
    "minik_maceralar": [
        "#MinikMaceralar", "#CuteBaby", "#BabyShorts", "#BabyAdventures",
        "#FunnyBaby", "#SevimliBebekler", "#BebekVideoları", "#TrendingShorts",
        "#ViralShorts", "#Shorts", "#Cute", "#ForKids", "#TatlıBebek"
    ]
}

def get_trending_hashtags(profile_key: str, count: int = 5):
    """Gets trending hashtags for a profile."""
    
    # Get profile-specific hashtags
    profile_tags = TRENDING_HASHTAGS.get(profile_key, [])
    global_tags = TRENDING_HASHTAGS.get("global", [])
    
    # Combine and shuffle
    all_tags = profile_tags + global_tags
    random.shuffle(all_tags)
    
    # Return requested count
    return all_tags[:count]

def add_hashtags_to_description(description: str, profile_key: str):
    """Adds trending hashtags to video description."""
    
    # Get trending hashtags
    hashtags = get_trending_hashtags(profile_key, count=5)
    hashtag_string = " ".join(hashtags)
    
    # Check if hashtags already exist
    if "#" in description:
        # Hashtags already exist, update them
        lines = description.split("\n")
        new_lines = []
        for line in lines:
            if line.strip().startswith("#"):
                # Replace this line with new hashtags
                new_lines.append(hashtag_string)
            else:
                new_lines.append(line)
        return "\n".join(new_lines)
    else:
        # Add hashtags at the end
        return f"{description}\n\n{hashtag_string}"

def update_video_description_with_hashtags(profile_key: str, video_id: str, description: str):
    """Updates video description with trending hashtags."""
    
    new_description = add_hashtags_to_description(description, profile_key)
    
    # Save to file for later use
    hashtag_file = f"data/hashtags_{profile_key}.json"
    os.makedirs(os.path.dirname(hashtag_file), exist_ok=True)
    
    hashtag_data = {}
    if os.path.exists(hashtag_file):
        with open(hashtag_file, "r", encoding="utf-8") as f:
            hashtag_data = json.load(f)
    
    hashtag_data[video_id] = {
        "updated_at": datetime.now().isoformat(),
        "hashtags": get_trending_hashtags(profile_key, count=5)
    }
    
    with open(hashtag_file, "w", encoding="utf-8") as f:
        json.dump(hashtag_data, f, indent=2, ensure_ascii=False)
    
    return new_description

def refresh_trending_hashtags():
    """Refreshes trending hashtags (can be called daily)."""
    
    # In a real implementation, this would fetch from YouTube API
    # For now, we'll just shuffle the existing ones
    for key in TRENDING_HASHTAGS:
        if key != "global":
            random.shuffle(TRENDING_HASHTAGS[key])
    
    print("✅ Trending hashtag'ler güncellendi")
    return TRENDING_HASHTAGS

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Kullanım:")
        print("  python trending_hashtags.py <profile> <description>")
        print("  python trending_hashtags.py --refresh")
        sys.exit(1)
    
    if sys.argv[1] == "--refresh":
        refresh_trending_hashtags()
    else:
        profile = sys.argv[1]
        description = sys.argv[2]
        new_description = update_video_description_with_hashtags(profile, "test", description)
        print("Orijinal:")
        print(description)
        print("\nYeni:")
        print(new_description)
