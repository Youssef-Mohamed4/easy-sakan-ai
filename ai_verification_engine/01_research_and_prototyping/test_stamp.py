import cv2
import numpy as np

def check_for_official_stamp(contract_path, stamp_path, min_match_count=40): # BUMPED TO 40
    print(f"🔍 Scanning {contract_path} for official stamp...")
    
    contract_img = cv2.imread(contract_path, cv2.IMREAD_GRAYSCALE)
    stamp_img = cv2.imread(stamp_path, cv2.IMREAD_GRAYSCALE)

    if contract_img is None or stamp_img is None:
        print("❌ Error loading images.")
        return False

    sift = cv2.SIFT_create()

    kp1, des1 = sift.detectAndCompute(stamp_img, None)
    kp2, des2 = sift.detectAndCompute(contract_img, None)

    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    good_matches = []
    for m, n in matches:
        # TIGHTENED RATIO TO 0.65 (Rejects generic text/lines)
        if m.distance < 0.65 * n.distance:
            good_matches.append(m)

    match_count = len(good_matches)
    print(f"-> Found {match_count} strong geometric matching points.")

    # --- VISUAL DEBUGGING: SEE WHAT THE AI SEES ---
    img_matches = cv2.drawMatches(
        stamp_img, kp1, 
        contract_img, kp2, 
        good_matches, None, 
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    
    # Save the visual debug image so you can look at it
    debug_filename = f"debug_sift_{contract_path}"
    cv2.imwrite(debug_filename, img_matches)
    print(f"📸 Saved visual debug map to '{debug_filename}'")
    # ----------------------------------------------

    if match_count >= min_match_count:
        print("✅ STAMP DETECTED! Document is officially stamped.")
        return True
    else:
        print("🚨 NO STAMP FOUND. Possible unofficial document.")
        return False

if __name__ == "__main__":
    # Test 1: The True Negative (Should fail)
    print("\n--- TEST 1: CLEAN ALGERIAN CONTRACT ---")
    check_for_official_stamp("real_contract_sample.jpg", "reference_stamp.jpg")