import csv

# Replace this with the path to your log file, or read your log as a string
log_file_path = 'log.txt'  # or None if using log string
log_string = None  # If you have the log as a string, assign it here

# Path to your original CSV
csv_file_path = 'devotional_post_tag_map.csv'
# Path for filtered output CSV
output_csv_path = 'devotional_post_tag_map_not_found.csv'

def extract_not_found_titles_from_log(log_lines):
    not_found_titles = set()
    for line in log_lines:
        if line.startswith("❌ Post not found:"):
            # Extract title after colon and strip whitespace
            title = line[len("❌ Post not found:"):].strip()
            if title:
                not_found_titles.add(title)
    return not_found_titles

def main():
    # Read log lines
    if log_file_path:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
    elif log_string:
        log_lines = log_string.splitlines()
    else:
        print("No log source provided")
        return

    not_found_titles = extract_not_found_titles_from_log(log_lines)
    print(f"Found {len(not_found_titles)} unique 'not found' post titles.")

    # Load original CSV and filter rows
    with open(csv_file_path, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        filtered_rows = [row for row in reader if row.get('title', '').strip() in not_found_titles]

    print(f"Filtered down to {len(filtered_rows)} posts matching 'not found' titles.")

    # Write filtered rows to new CSV
    if filtered_rows:
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=filtered_rows[0].keys())
            writer.writeheader()
            writer.writerows(filtered_rows)
        print(f"Filtered CSV saved as: {output_csv_path}")
    else:
        print("No matching posts found in CSV for the 'not found' titles.")

if __name__ == "__main__":
    main()
