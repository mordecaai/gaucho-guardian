# import needed modules
import json
import os
from datetime import datetime

# --- 1. AUTO-SETUP FOLDERS ---
# These folders act as the input for our data pipeline.
CURRENT_CLASSES_FOLDER = "current_classes"
POTENTIAL_CLASSES_FOLDER = "potential_classes"

# Ensure directories exist so the script doesn't crash on the first run.
# If they don't exist, we create those folders and print a message.
# Uncomment the following lines to enable said functionality.
#
# for folder in [CURRENT_CLASSES_FOLDER, POTENTIAL_CLASSES_FOLDER]:
#     if not os.path.exists(folder):
#         os.makedirs(folder)
#         print(f"📁 Created missing folder: {folder}")

# --- 2. CONFIGURATION ---
# These allow you to toggle global predefined requirements. Setting to None/False ignores the check.
TARGET_SUBJECT = False 
TARGET_GE = False 
REQUIRE_ONLINE = None

# --- 3. CORE LOGIC FUNCTIONS ---

def is_overlapping(start1, end1, start2, end2):
    """Calculates if two time windows clash using 24hr string comparison."""
    fmt = "%H:%M"
    try:
        s1, e1 = datetime.strptime(start1, fmt), datetime.strptime(end1, fmt)
        s2, e2 = datetime.strptime(start2, fmt), datetime.strptime(end2, fmt)
        return s1 < e2 and e1 > s2
    except: 
        return False

def generate_blackout_from_folder(folder_path):
    """
    Iterates through all 'Current' class JSONs to build a master 
    dictionary of times when the student is busy.
    """
    blackout = {"M": [], "T": [], "W": [], "R": [], "F": []}
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    
    for filename in files:
        with open(os.path.join(folder_path, filename), 'r') as f:
            data = json.load(f)
            # We look at 'classSections' to find specific meeting times
            for section in data.get("classSections", []):
                for loc in section.get("timeLocations", []):
                    days = (loc.get("days") or "").strip()
                    start, end = loc.get("beginTime"), loc.get("endTime")
                    if start and end:
                        for day in days:
                            if day in blackout:
                                # Append the busy window to the specific day's list
                                blackout[day].append((start, end))
    return blackout

def has_time_conflict(section, blackout_schedule):
    """Compares a single potential section against the busy schedule."""
    time_locs = section.get("timeLocations") or []
    for loc in time_locs:
        days, start, end = (loc.get("days") or "").strip(), loc.get("beginTime"), loc.get("endTime")
        if not all([days, start, end]): 
            continue
        for day in days:
            if day in blackout_schedule:
                # Check every blackout window registered for that day
                for b_start, b_end in blackout_schedule[day]:
                    if is_overlapping(start, end, b_start, b_end):
                        return True, f"Conflict on {day}"
    return False, ""

def check_class(data, blackout):
    """
    The main filter. It checks Subject/GE first, then iterates through 
    every section to find at least one that is both open AND conflict-free.
    """
    course_id = data.get("courseId", "Unknown")
    
    # Check global filters
    if TARGET_SUBJECT and (data.get("subjectArea") or "").strip() != TARGET_SUBJECT:
        return False, [], ["Wrong Subject"]
    
    valid_codes = []
    rejection_counts = {"Full": 0, "Conflict": 0}
    
    for section in data.get("classSections", []):
        enrolled, max_cap = section.get("enrolledTotal") or 0, section.get("maxEnroll") or 0
        
        # Priority 1: Is there a seat?
        if enrolled >= max_cap:
            rejection_counts["Full"] += 1
            continue
            
        # Priority 2: Does it fit the schedule?
        conflict, _ = has_time_conflict(section, blackout)
        if conflict:
            rejection_counts["Conflict"] += 1
            continue
            
        # If both pass, this is a viable enroll code
        valid_codes.append(section.get("enrollCode"))
            
    # Compile a list of why this course didn't work (if it failed)
    reasons = [f"{v} {k}" for k, v in rejection_counts.items() if v > 0]
    return (True if valid_codes else False), valid_codes, reasons

# --- 4. MAIN EXECUTION ---

print("🛠️ Step 1: Building Blackout Schedule from 'current_classes'...")
current_blackout = generate_blackout_from_folder(CURRENT_CLASSES_FOLDER)

# String arrays for quick logs
true_array = []
false_array = []

# Data arrays for True results (Passed)
true_raw_json = []        # Unchanged
true_modified_json = []   # With extra data on sections + section times

# Data arrays for False results (Rejected)
false_raw_json = []       # Unchanged
false_modified_json = []  # With rejection reasons

print("\n🔍 Step 2: Checking potential classes against schedule...")
potential_files = [f for f in os.listdir(POTENTIAL_CLASSES_FOLDER) if f.endswith(".json")]

for filename in potential_files:
    path = os.path.join(POTENTIAL_CLASSES_FOLDER, filename)
    with open(path, 'r') as f:
        data = json.load(f)
        course_id = data.get("courseId", "Unknown")
        
        works, sections, reasons = check_class(data, current_blackout)
        
        if works:
            section_str = ", ".join(sections)
            print(f"✅ {course_id} WORKS! (Valid sections: {section_str})")
            
            # --- Extract times for console and modified JSON ---
            readable_times = {} 
            for section in data.get("classSections", []):
                code = section.get("enrollCode")
                if code in sections:
                    times_list = []
                    for loc in (section.get("timeLocations") or []):
                        d, s, e = loc.get("days", "").strip(), loc.get("beginTime", ""), loc.get("endTime", "")
                        times_list.append(f"{d} {s}-{e}")
                    
                    time_summary = " | ".join(times_list)
                    readable_times[code] = time_summary
                    print(f"   👉 Section {code}: {time_summary}")
            
            # Update Arrays
            true_array.append(course_id)
            true_raw_json.append(data)
            
            mod_data = data.copy()
            mod_data["passingEnrollCodes"] = sections
            mod_data["sectionTimesSummary"] = readable_times
            true_modified_json.append(mod_data)

        else:
            reason_str = ", ".join(reasons) if reasons else "Filter Mismatch"
            print(f"❌ {course_id} REJECTED ({reason_str})")
            
            false_array.append(course_id)
            false_raw_json.append(data)
            
            mod_fail = data.copy()
            mod_fail["rejectionReasons"] = reasons
            false_modified_json.append(mod_fail)

# --- 5. FINAL OUTPUT & EXPORT ---
print("\n")
print("=" * 50) #adding headers to separate the summary from the more detailed logs
print(f"RESULTS SUMMARY:")
print(f"Passed: {true_array}")
print(f"Failed: {false_array}")
print("=" * 50) #adding footers

# Master Export
master_results = {
    "passed": {"raw": true_raw_json, "modified": true_modified_json},
    "failed": {"raw": false_raw_json, "modified": false_modified_json}
}

with open("master_course_results.json", "w") as f:
    json.dump(master_results, f, indent=4)
    print("\n📄 Master data exported to 'master_course_results.json'")