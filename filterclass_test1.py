import json
from datetime import datetime

"""
This script filters a UCSB course JSON file based on hardcoded variables.
It checks for Subject, GE Area, and Online status, then scans each section
for enrollment space and time conflicts against a 'Blackout' schedule.
If a course is rejected, it provides specific reasons.
"""

# --- CONFIGURATION (Change these to your needs) ---
TARGET_SUBJECT = ("phys").upper()  # Set to the desired subject area (e.g., "MATH", "PHYS", "ECE", etc.)
TARGET_GE = None  # Set to None (not a string) to skip GE filtering
REQUIRE_ONLINE = False  # Set to True to require online courses, False to ignore this filter


# Blackout windows (M=Monday, T=Tuesday, W=Wednesday, R=Thursday, F=Friday)
BLACKOUT_SCHEDULE = {
    "M": [("08:00", "09:00"), ("12:00", "13:30"), ("17:00", "19:00")],
    "T": [("12:00", "14:00"), ("15:30", "16:45")],
    "W": [("08:00", "09:00"), ("12:00", "13:30")],
    "R": [("12:00", "14:00")],
    "F": []
}


def is_overlapping(start1, end1, start2, end2):
    """Checks if two 24hr time ranges overlap."""
    fmt = "%H:%M"
    s1 = datetime.strptime(start1, fmt)
    e1 = datetime.strptime(end1, fmt)
    s2 = datetime.strptime(start2, fmt)
    e2 = datetime.strptime(end2, fmt)
    return s1 < e2 and e1 > s2

def has_time_conflict(section):
    """Returns (True, reason) if a conflict/error exists, else (False, '')."""
    time_locs = section.get("timeLocations", [])
    
    # Treat missing time data as an error
    if not time_locs:
        return True, "No time data found (TBA?)" 

    for loc in time_locs:
        days = loc.get("days", "").strip()
        start = loc.get("beginTime")
        end = loc.get("endTime")

        if not start or not end or not days:
            return True, "Incomplete time or day information"

        for day_char in days:
            if day_char in BLACKOUT_SCHEDULE:
                for b_start, b_end in BLACKOUT_SCHEDULE[day_char]:
                    if is_overlapping(start, end, b_start, b_end):
                        return True, f"Conflict on {day_char} at {start}-{end}"
    return False, ""

def report_success(data, valid_sections, warnings, all_ges):
    """Prints a detailed success summary."""
    print(f"\n{'='*50}")
    print(f"✨ MATCH FOUND: {data.get('courseId')}")
    print(f"📘 Title: {data.get('title')}")
    print(f"🎓 GE Areas: {', '.join(all_ges) if all_ges else 'None'}")
    
    # Identify the primary lecture
    lecture = next((s for s in data.get("classSections", []) if s.get("secondaryStatus") is None), None)
    if lecture:
        print(f"\n📚 Main Lecture (Section {lecture.get('section')}):")
        for loc in lecture.get("timeLocations", []):
            print(f"   🕒 {loc.get('days')} {loc.get('beginTime')} - {loc.get('endTime')}")

    print(f"\n📍 Valid Sections to Join:")
    for match in valid_sections:
        print(f"   ✅ Section {match.get('section')} (Code: {match.get('enrollCode')})")
        for loc in match.get("timeLocations", []):
            print(f"      🕒 {loc.get('days')} {loc.get('beginTime')} - {loc.get('endTime')}")
    
    if warnings:
        print(f"\n⚠️ WARNING: Sections skipped due to missing data: {', '.join(warnings)}")
    print(f"{'='*50}\n")

def test_single_json(file_path):
    """The main execution flow for a single JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find file '{file_path}'")
        return

    course_id = data.get("courseId", "Unknown Course")
    
    # --- 1. Course-level Filters ---
    if data.get("subjectArea", "").strip() != TARGET_SUBJECT:
        print(f"❌ {course_id} Rejected: Wrong Subject Area")
        return

    ge_codes = [ge.get("geCode") for ge in data.get("generalEducation", [])]
    if TARGET_GE and TARGET_GE not in ge_codes:
        print(f"❌ {course_id} Rejected: Missing GE Area {TARGET_GE} (Offers: {ge_codes})")
        return

    if REQUIRE_ONLINE and not data.get("onLineCourse"):
        print(f"❌ {course_id} Rejected: Not an Online Course")
        return

    # --- 2. Section-level Filters ---
    valid_sections = []
    warnings = []
    rejection_reasons = []
    
    for section in data.get("classSections", []):
        code = section.get("enrollCode")
        
        # Space Check
        # Using 'or 0' ensures that if the value is None, it defaults to 0
        enrolled = section.get("enrolledTotal") or 0
        max_cap = section.get("maxEnroll") or 0

        
        
        if enrolled >= max_cap:
            rejection_reasons.append(f"Section {code}: Full ({enrolled}/{max_cap})")
            continue
        
            
        # Conflict Check
        conflict, reason = has_time_conflict(section)
        if conflict:
            if "No time data" in reason:
                warnings.append(code)
            rejection_reasons.append(f"Section {code}: {reason}")
            continue
        
        valid_sections.append(section)

    # --- 3. Final Report ---
    if valid_sections:
        report_success(data, valid_sections, warnings, ge_codes)
    else:
        print(f"❌ {course_id} Rejected: No valid sections found.")
        for r in rejection_reasons:
            print(f"   - {r}")

# To run, ensure your JSON file is named 'course.json' or change the name here:
# test_single_json('course.json')
#test_single_json('class_11593.json')  # Example file name, change as needed

# Instead of one file, do a list:
my_files = ['class_11593.json', 'class_29496.json', 'class_38687.json']

for file in my_files:
    test_single_json(file)