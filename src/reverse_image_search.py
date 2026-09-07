import os
import requests

from dotenv import load_dotenv

# Works both when running:
# python src/reverse_image_search.py
# and when importing from Flask:
# from src.reverse_image_search import reverse_image_search

try:
    from src.blockchain import register_social_match
except ModuleNotFoundError:
    from blockchain import register_social_match


# --------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

SERPAPI_IMAGE_URL = "https://serpapi.com/image"
SERPAPI_SEARCH_URL = "https://serpapi.com/search"


# --------------------------------------------------
# SOCIAL MEDIA DOMAINS
# --------------------------------------------------

SOCIAL_DOMAINS = {
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "x.com": "X",
    "twitter.com": "X",
    "tiktok.com": "TikTok",
    "linkedin.com": "LinkedIn",
    "youtube.com": "YouTube",
}


# --------------------------------------------------
# CHECK API KEY
# --------------------------------------------------

def check_api_key():

    if not SERPAPI_KEY:

        return {
            "success": False,
            "message": "SERPAPI_KEY is not configured."
        }

    return {
        "success": True
    }


# --------------------------------------------------
# UPLOAD IMAGE TO SERPAPI
# --------------------------------------------------

def upload_image(image_path):

    key_status = check_api_key()

    if not key_status["success"]:
        return key_status

    if not os.path.exists(image_path):

        return {
            "success": False,
            "message": f"Image not found: {image_path}"
        }

    try:

        with open(image_path, "rb") as image_file:

            response = requests.post(
                SERPAPI_IMAGE_URL,
                files={
                    "image": image_file
                },
                data={
                    "api_key": SERPAPI_KEY
                },
                timeout=60
            )

        response.raise_for_status()

        data = response.json()

        if "error" in data:

            return {
                "success": False,
                "message": data["error"]
            }

        image_id = data.get("image_id")

        if not image_id:

            return {
                "success": False,
                "message": "SerpApi did not return an image ID."
            }

        return {
            "success": True,
            "image_id": image_id
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Image upload failed: {str(error)}"
        }


# --------------------------------------------------
# GOOGLE LENS SEARCH
# --------------------------------------------------

def search_google_lens(image_id):

    key_status = check_api_key()

    if not key_status["success"]:
        return key_status

    try:

        response = requests.get(
            SERPAPI_SEARCH_URL,
            params={
                "engine": "google_lens",
                "image_id": image_id,
                "type": "all",
                "hl": "en",
                "safe": "active",
                "api_key": SERPAPI_KEY
            },
            timeout=90
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:

            return {
                "success": False,
                "message": data["error"]
            }

        return {
            "success": True,
            "results": data
        }

    except Exception as error:

        return {
            "success": False,
            "message": f"Google Lens search failed: {str(error)}"
        }


# --------------------------------------------------
# FIND SOCIAL MEDIA MATCHES
# --------------------------------------------------

def find_social_matches(results):

    matches = []

    exact_matches = results.get(
        "exact_matches",
        []
    )

    visual_matches = results.get(
        "visual_matches",
        []
    )

    # --------------------------------------------------
    # IMPORTANT:
    # Preserve whether Google Lens classified the
    # result as an exact match or visual match.
    # --------------------------------------------------

    all_results = []

    for result in exact_matches:

        result["_match_type"] = "exact_match"

        all_results.append(result)

    for result in visual_matches:

        result["_match_type"] = "visual_match"

        all_results.append(result)

    seen_urls = set()

    for result in all_results:

        link = result.get("link")

        if not link:
            continue

        link_lower = link.lower()

        platform = None

        for domain, name in SOCIAL_DOMAINS.items():

            if domain in link_lower:

                platform = name
                break

        if not platform:
            continue

        if link in seen_urls:
            continue

        seen_urls.add(link)

        matches.append({

            "platform": platform,

            "match_type": result.get(
                "_match_type",
                "unknown"
            ),

            "title": result.get(
                "title",
                "Untitled"
            ),

            "url": link,

            "source": result.get(
                "source",
                platform
            ),

            "thumbnail": result.get(
                "thumbnail"
            )
        })

    return matches


# --------------------------------------------------
# CHOOSE BEST SOCIAL MEDIA MATCH
# --------------------------------------------------

def choose_best_social_match(matches):
    """
    Select the strongest genuine social-media result.

    Priority:
        1. Exact Google Lens matches
        2. Direct social-media posts/videos/reels
        3. Visual matches
        4. Generic/profile pages are penalized
    """

    scored = []

    for match in matches:

        url = match.get(
            "url",
            ""
        ).lower()

        title = match.get(
            "title",
            ""
        ).lower()

        match_type = match.get(
            "match_type",
            "unknown"
        )

        score = 0

        # --------------------------------------------------
        # GOOGLE LENS MATCH TYPE
        # --------------------------------------------------

        if match_type == "exact_match":

            score += 100

        elif match_type == "visual_match":

            score += 20

        # --------------------------------------------------
        # DIRECT INSTAGRAM POSTS / REELS
        # --------------------------------------------------

        if "/reel/" in url:

            score += 15

        if "/p/" in url:

            score += 15

        # --------------------------------------------------
        # DIRECT FACEBOOK POSTS / VIDEOS
        # --------------------------------------------------

        if "/posts/" in url:

            score += 15

        if "/videos/" in url:

            score += 15

        # Facebook group post

        if (
            "facebook.com" in url
            and "/groups/" in url
        ):

            score += 10

        # --------------------------------------------------
        # DIRECT X POST
        # --------------------------------------------------

        if "/status/" in url:

            score += 15

        # --------------------------------------------------
        # DIRECT YOUTUBE VIDEO
        # --------------------------------------------------

        if "/watch?v=" in url:

            score += 15

        if "/shorts/" in url:

            score += 15

        # --------------------------------------------------
        # DIRECT TIKTOK VIDEO
        # --------------------------------------------------

        if "/video/" in url:

            score += 15

        # --------------------------------------------------
        # PENALIZE GENERIC PAGES
        # --------------------------------------------------

        if "/discover/" in url:

            score -= 15

        if "/search" in url:

            score -= 15

        # --------------------------------------------------
        # PENALIZE OBVIOUS FACEBOOK PROFILE PAGES
        # --------------------------------------------------

        if (
            "facebook.com" in url
            and "/posts/" not in url
            and "/videos/" not in url
            and "/groups/" not in url
        ):

            score -= 10

        # --------------------------------------------------
        # PENALIZE GENERIC TIKTOK PAGES
        # --------------------------------------------------

        if (
            "tiktok.com" in url
            and "/video/" not in url
            and "/discover/" in url
        ):

            score -= 10

        # --------------------------------------------------
        # TITLE BONUS
        # --------------------------------------------------

        if title.strip():

            score += 2

        scored.append(
            (
                score,
                match
            )
        )

    # --------------------------------------------------
    # SORT HIGHEST SCORE FIRST
    # --------------------------------------------------

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    if not scored:

        return None

    return scored[0][1]


# --------------------------------------------------
# COMPLETE REVERSE IMAGE SEARCH
# --------------------------------------------------

def reverse_image_search(image_path):

    print()

    print("=" * 60)
    print("        REVERSE IMAGE SEARCH")
    print("=" * 60)

    # --------------------------------------------------
    # STEP 1: UPLOAD IMAGE
    # --------------------------------------------------

    print()
    print("[1/5] Uploading image to SerpApi...")

    upload_result = upload_image(
        image_path
    )

    if not upload_result["success"]:

        print(
            "ERROR:",
            upload_result["message"]
        )

        return upload_result

    image_id = upload_result["image_id"]

    print(
        "Image uploaded successfully."
    )

    print(
        "Image ID:",
        image_id
    )

    # --------------------------------------------------
    # STEP 2: GOOGLE LENS
    # --------------------------------------------------

    print()
    print("[2/5] Searching Google Lens...")

    search_result = search_google_lens(
        image_id
    )

    if not search_result["success"]:

        print(
            "ERROR:",
            search_result["message"]
        )

        return search_result

    results = search_result["results"]

    print(
        "Google Lens search completed."
    )

    # --------------------------------------------------
    # STEP 3: FIND SOCIAL MEDIA MATCHES
    # --------------------------------------------------

    print()
    print("[3/5] Finding social-media matches...")

    social_matches = find_social_matches(
        results
    )

    print()
    print(
        "Social media matches found:",
        len(social_matches)
    )

    # --------------------------------------------------
    # DISPLAY MATCHES
    # --------------------------------------------------

    for index, match in enumerate(
        social_matches,
        start=1
    ):

        print()

        print(
            f"{index}. "
            f"{match['platform']}"
        )

        print(
            "   Match type:",
            match["match_type"]
        )

        print(
            "   Title:",
            match["title"]
        )

        print(
            "   URL:",
            match["url"]
        )

    # --------------------------------------------------
    # STEP 4: SELECT BEST MATCH
    # --------------------------------------------------

    blockchain_record = None
    best_match = None

    if social_matches:

        print()
        print(
            "[4/5] Selecting strongest social-media match..."
        )

        best_match = choose_best_social_match(
            social_matches
        )

        print()
        print("=" * 60)
        print("        BEST SOCIAL MEDIA MATCH")
        print("=" * 60)

        print(
            "Platform:",
            best_match["platform"]
        )

        print(
            "Match type:",
            best_match["match_type"]
        )

        print(
            "Title:",
            best_match["title"]
        )

        print(
            "URL:",
            best_match["url"]
        )

                # --------------------------------------------------
        # STEP 5: WRITE VERIFIED EXACT MATCH TO BLOCKCHAIN
        # --------------------------------------------------

        if best_match["match_type"] == "exact_match":

            print()
            print(
                "[5/5] Exact match confirmed."
            )

            print(
                "Writing verified match to blockchain..."
            )

            blockchain_record = register_social_match(

    identity_id="FACE-REVERSE-001",

    platform=best_match["platform"],

    title=best_match["title"],

    url=best_match["url"],

    match_type=best_match["match_type"]
)

            print()
            print("=" * 60)
            print("        VERIFIED BLOCKCHAIN RECORD")
            print("=" * 60)

            print(
                "Match type:",
                best_match["match_type"]
            )

            print(
                "Block index:",
                blockchain_record["index"]
            )

            print(
                "Block hash:",
                blockchain_record["hash"]
            )

            print(
                "Previous hash:",
                blockchain_record["previous_hash"]
            )

        else:

            print()
            print(
                "[5/5] No exact social-media match confirmed."
            )

            print(
                "Best result was only:",
                best_match["match_type"]
            )

            print(
                "Blockchain write skipped."
            )

    # --------------------------------------------------
    # COMPLETE RESULT
    # --------------------------------------------------

    return {

        "success": True,

        "image_id": image_id,

        "social_matches": social_matches,

        "total_matches": len(
            social_matches
        ),

        "best_match": best_match,

        "blockchain_record": blockchain_record
    }


# --------------------------------------------------
# TEST THE SCRIPT DIRECTLY
# --------------------------------------------------

if __name__ == "__main__":

    test_image = os.path.join(
        "input",
        "test.jpg"
    )

    result = reverse_image_search(
        test_image
    )

    print()
    print("=" * 60)
    print("        FINAL RESULT")
    print("=" * 60)

    print(
        result
    )
    
    if __name__ == "__main__":

        test_image = os.path.join(
        "input",
        "test2.jpg"
         )

        result = reverse_image_search(
        test_image
         )