import os
import subprocess
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# -----------------------------
# CONFIGURATION
# -----------------------------
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'}
FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"
MAX_THREADS = 4  # adjust to CPU cores

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_media_info(file_path):
    """Get media info using ffprobe."""
    cmd = [FFPROBE_PATH, "-v", "error", "-show_streams", "-print_format", "json", str(file_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return None

def fast_decode_check(file_path, stream_index=None, stream_type=None):
    """
    Perform a fast decode check using -c copy.
    Returns (status, optional info string)
    """
    cmd = [FFMPEG_PATH, "-v", "-hwaccel nvdec", "error", "-i", str(file_path)]
    if stream_index is not None:
        cmd += ["-map", f"0:{stream_index}"]
    cmd += ["-c", "copy", "-f", "null", "-"]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return "Playable", None
    except subprocess.CalledProcessError as e:
        stderr = e.stderr
        first_error_time = None
        # Try to find approximate location from frame/time info
        for line in stderr.splitlines():
            if "time=" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("time="):
                        first_error_time = part.replace("time=", "")
                        break
            if first_error_time:
                break
        if first_error_time:
            return "Partially Corrupted", f"first error at {first_error_time}"
        else:
            if stream_type == "subtitle":
                return "Not Fully Readable", None
            return "Broken", "location unknown"

def process_file(full_path):
    """Process a single file and return results dict plus formatted string."""
    report_lines = [f"Analyzing: {full_path}\n"]
    info = get_media_info(full_path)
    
    if not info or "streams" not in info:
        report_lines.append("File is unreadable (ffprobe failed)\n")
        return {
            "file": str(full_path),
            "video_status": "Broken",
            "audio_status": [],
            "subtitle_status": []
        }, "\n".join(report_lines)

    video_status, video_info = "No Video Stream", None
    audio_status_list, subtitle_status_list = [], []

    for stream in info.get("streams", []):
        codec_name = stream.get("codec_name", "unknown")
        index = stream.get("index", -1)
        stype = stream.get("codec_type", "unknown")

        if stype == "video":
            report_lines.append(f" -> Validating video stream ({codec_name})...")
            video_status, video_info = fast_decode_check(full_path, index, "video")
            if video_info:
                report_lines.append(f"{video_status.upper()} | {video_info}")
            else:
                report_lines.append(f"{video_status.upper()}")
        elif stype == "audio":
            report_lines.append(f" -> Validating audio track {index} ({codec_name})...")
            status, info_msg = fast_decode_check(full_path, index, "audio")
            if info_msg:
                report_lines.append(f"{status.upper()} | {info_msg}")
            else:
                report_lines.append(f"{status.upper()}")
            audio_status_list.append({"index": index, "codec": codec_name, "status": status})
        elif stype == "subtitle":
            report_lines.append(f" -> Validating subtitle track {index} ({codec_name})...")
            status, info_msg = fast_decode_check(full_path, index, "subtitle")
            if info_msg:
                report_lines.append(f"{status.upper()} | {info_msg}")
            else:
                report_lines.append(f"{status.upper()}")
            subtitle_status_list.append({"index": index, "codec": codec_name, "status": status})

    # Only do these checks if info exists
    streams = info.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams):
        video_status = "No Video Stream"
    if not any(s.get("codec_type") == "audio" for s in streams):
        audio_status_list = []
    if not any(s.get("codec_type") == "subtitle" for s in streams):
        subtitle_status_list = []

    return {
        "file": str(full_path),
        "video_status": video_status,
        "video_info": video_info,
        "audio_status": audio_status_list,
        "subtitle_status": subtitle_status_list
    }, "\n".join(report_lines)


# -----------------------------
# MAIN SCAN FUNCTION
# -----------------------------
def scan_folder(folder_path):
    report, counts = [], {"Playable": 0, "Partially Corrupted": 0, "Broken": 0, "No Video Stream": 0}
    files_to_scan = [Path(root) / f for root, _, files in os.walk(folder_path)
                     for f in files if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

    print(f"Found {len(files_to_scan)} video files to scan in {folder_path}\n")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_file = {executor.submit(process_file, f): f for f in files_to_scan}

        for future in tqdm(as_completed(future_to_file), total=len(files_to_scan), desc="CineScan Progress"):
            result, report_text = future.result()
            report.append(result)

            # Save individual TXT file
            movie_txt = Path(result["file"]).with_suffix(".txt")
            with open(movie_txt, "w", encoding="utf-8") as f:
                f.write(report_text)

            # Update counts
            status = result["video_status"]
            if status in counts:
                counts[status] += 1
            elif status == "Playable" and all(a["status"]=="Playable" for a in result["audio_status"]):
                counts["Playable"] +=1
            else:
                counts["Partially Corrupted"] +=1

    # Save combined report
    report_file = Path(folder_path) / "cine_scan_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\nScan complete!")
    print(f"Combined report saved to: {report_file}")
    print(f"Summary: {counts}")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    folder_to_scan = input("Enter folder path to scan: ").strip()
    scan_folder(folder_to_scan)
