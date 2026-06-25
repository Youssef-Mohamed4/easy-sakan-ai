import re

def normalize_arabic(text: str) -> str:
    """Cleans OCR text and normalizes Arabic variants."""
    if not text: 
        return ""
    
    # 1. Normalize characters
    text = re.sub('[إأآا]', 'ا', text)
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    text = text.replace('ـ', '')
    
    # 2. Fix compound names (عبد الحميد -> عبدالحميد)
    text = re.sub(r'عبد\s+([\u0600-\u06FF]+)', r'عبد\1', text)
    
    # 3. Strip out everything except Arabic letters and spaces
    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    
    # 4. Remove single-letter OCR noise
    words = [w for w in text.split() if len(w) > 1]
    
    return " ".join(words)

def is_name_match(ocr_text_1: str, ocr_text_2: str, min_matching_words: int = 3) -> bool:
    """Finds intersecting name words while ignoring document boilerplate."""
    if not ocr_text_1 or not ocr_text_2:
        return False
        
    t1 = normalize_arabic(ocr_text_1).split()
    t2 = normalize_arabic(ocr_text_2).split()
    
    # 1. Domain-specific stop words (Egyptian IDs and University boilerplate)
    stop_words = {
        "بطاقه", "تحقيق", "الشخصيه", "جمهوريه", "مصر", "العربيه",
        "كليه", "جامعه", "معهد", "اكاديميه", "كارنيه", "المكتبه", "كود",
        "طالب", "الطالب", "المستوي", "الفرقه", "الترم", "الفصل", "الدراسي",
        "الاول", "الثاني", "الثالث", "الرابع", "الخامس", "قسم", "نظم", 
        "المعلومات", "وعلوم", "الحاسب", "هندسه", "برنامج", "خاص", "يعتمد",
        "محافظه", "مركز", "مدينه", "شارع", "الرقم", "القومي", "عميد", "رئيس",
        "البريد", "الالكتروني", "وزاره", "الداخليه"
    }
    
    # 2. Get unique words in both texts that are NOT stop words
    words_1 = set(w for w in t1 if w not in stop_words)
    words_2 = set(w for w in t2 if w not in stop_words)
    
    # 3. Find the exact intersecting names
    matched_words = words_1.intersection(words_2)
    
    print(f"  [Name Match] Extracted Shared Names: {matched_words}")
    print(f"  [Name Match] Matched Count: {len(matched_words)} (Required: {min_matching_words})")
    
    # If they share at least 3 names (e.g., محمود, احمد, السيد) -> Match!
    return len(matched_words) >= min_matching_words