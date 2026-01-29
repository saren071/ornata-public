import datetime
import math
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# --- CONFIGURATION ---
TARGET_PATH: str = os.path.join("src", "ornata")
OUTPUT_FILE: str = "ornata_deep_analysis.txt"
SKIP_DIRS: set[str] = {'.git', '__pycache__', 'node_modules', '.venv', '.idea', '.vscode', 'dist', 'build'}

# --- TYPE DEFINITIONS ---

@dataclass
class FileMetrics:
    path: str
    extension: str
    size_bytes: int
    created_at: float
    modified_at: float
    is_binary: bool
    line_count: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    entropy: float = 0.0
    indent_style: str = "None"  # 'Spaces', 'Tabs', 'Mixed', 'None'
    avg_line_length: float = 0.0
    max_line_length: int = 0

@dataclass
class ProjectReport:
    total_files: int = 0
    total_size_bytes: int = 0
    total_lines: int = 0
    total_code: int = 0
    total_comments: int = 0
    total_blanks: int = 0
    binary_file_count: int = 0
    text_file_count: int = 0
    
    # Aggregates
    files_by_extension: dict[str, list[FileMetrics]] = field(default_factory=lambda: defaultdict(list))
    files_by_depth: Counter[int] = field(default_factory=Counter)
    indentation_stats: Counter[str] = field(default_factory=Counter)
    
    # Extremes
    oldest_file: FileMetrics | None = None
    newest_file: FileMetrics | None = None
    largest_file: FileMetrics | None = None
    highest_entropy_file: FileMetrics | None = None

# --- UTILITIES ---

def calculate_entropy(data: bytes) -> float:
    """Calculates Shannon Entropy to determine information density."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    seen = Counter(data)
    for count in seen.values():
        p_x = count / length
        entropy -= p_x * math.log2(p_x)
    return entropy

def detect_indentation(lines: list[str]) -> str:
    """Heuristic to detect indentation style."""
    space_indents = 0
    tab_indents = 0
    for line in lines:
        if line.startswith(' '):
            space_indents += 1
        elif line.startswith('\t'):
            tab_indents += 1
    
    if space_indents > 0 and tab_indents > 0:
        return "Mixed"
    if space_indents > tab_indents:
        return "Spaces"
    if tab_indents > space_indents:
        return "Tabs"
    return "None"

def is_binary_content(data: bytes) -> bool:
    """Checks for null bytes to detect binary files."""
    if b'\0' in data:
        return True
    return False

def get_comment_marker(ext: str) -> str | None:
    """Returns the comment marker for a given extension."""
    mapping = {
        '.py': '#', '.sh': '#', '.yaml': '#', '.yml': '#', '.toml': '#',
        '.js': '//', '.ts': '//', '.jsx': '//', '.tsx': '//', 
        '.java': '//', '.c': '//', '.cpp': '//', '.cs': '//', '.go': '//', '.rs': '//',
        '.html': '<!--', '.xml': '<!--', '.css': '/*', '.scss': '//'
    }
    return mapping.get(ext.lower())

# --- ANALYSIS LOGIC ---

def analyze_file(file_path: Path) -> FileMetrics:
    stats = file_path.stat()
    ext = file_path.suffix.lower() or "(no_ext)"
    
    metrics = FileMetrics(
        path=str(file_path),
        extension=ext,
        size_bytes=stats.st_size,
        created_at=stats.st_ctime,
        modified_at=stats.st_mtime,
        is_binary=False
    )

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            
        metrics.entropy = calculate_entropy(raw_data)
        metrics.is_binary = is_binary_content(raw_data[:8192]) # Check first 8KB

        if not metrics.is_binary:
            # Decode text
            try:
                content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1 if utf-8 fails, or treat as binary if strict
                content = raw_data.decode('latin-1', errors='replace')

            lines = content.splitlines()
            metrics.line_count = len(lines)
            metrics.indent_style = detect_indentation(lines)
            
            if lines:
                metrics.max_line_length = max(len(line) for line in lines)
                metrics.avg_line_length = sum(len(line) for line in lines) / len(lines)

            marker = get_comment_marker(ext)
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics.blank_lines += 1
                elif marker and stripped.startswith(marker):
                    metrics.comment_lines += 1
                else:
                    metrics.code_lines += 1
    except Exception as e:
        # Permission errors or other IO issues
        print(f"Skipping file read for {file_path}: {e}")
        metrics.is_binary = True # Assume binary/unreadable to be safe

    return metrics

def walk_and_analyze(target_dir: str, skip_dirs: set[str]) -> ProjectReport:
    report: ProjectReport = ProjectReport()
    
    if not os.path.exists(target_dir):
        print(f"CRITICAL ERROR: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    print(f"Starting strict analysis on: {os.path.abspath(target_dir)}")
    
    for root, dirs, files in os.walk(target_dir):
        # In-place filtering of directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        depth = root.count(os.sep) - target_dir.count(os.sep)
        
        for file in files:
            full_path = Path(root) / file
            metrics = analyze_file(full_path)
            
            # Update Report Aggregates
            report.total_files += 1
            report.total_size_bytes += metrics.size_bytes
            report.files_by_extension[metrics.extension].append(metrics)
            report.files_by_depth[depth] += 1
            
            if metrics.is_binary:
                report.binary_file_count += 1
            else:
                report.text_file_count += 1
                report.total_lines += metrics.line_count
                report.total_code += metrics.code_lines
                report.total_comments += metrics.comment_lines
                report.total_blanks += metrics.blank_lines
                report.indentation_stats[metrics.indent_style] += 1

            # Track Extremes
            if not report.largest_file or metrics.size_bytes > report.largest_file.size_bytes:
                report.largest_file = metrics
            
            if not report.oldest_file or metrics.created_at < report.oldest_file.created_at:
                report.oldest_file = metrics
                
            if not report.newest_file or metrics.modified_at > report.newest_file.modified_at:
                report.newest_file = metrics
            
            if not report.highest_entropy_file or metrics.entropy > report.highest_entropy_file.entropy:
                report.highest_entropy_file = metrics

    return report

# --- OUTPUT GENERATION ---

def format_bytes(size: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def write_report(report: ProjectReport, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ORNATA PROJECT DEEP ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

        f.write("1. EXECUTIVE SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Files Scanned:    {report.total_files}\n")
        f.write(f"Total Project Size:     {format_bytes(report.total_size_bytes)}\n")
        f.write(f"Text Files:             {report.text_file_count}\n")
        f.write(f"Binary Files:           {report.binary_file_count}\n")
        f.write(f"Total Lines of Text:    {report.total_lines:,}\n")
        if report.total_lines > 0:
            f.write(f"  - Code Lines:         {report.total_code:,} ({report.total_code/report.total_lines:.1%})\n")
            f.write(f"  - Comments:           {report.total_comments:,} ({report.total_comments/report.total_lines:.1%})\n")
            f.write(f"  - Whitespace:         {report.total_blanks:,} ({report.total_blanks/report.total_lines:.1%})\n")
        f.write("\n")

        f.write("2. FILE TYPE BREAKDOWN (Detailed)\n")
        f.write("-" * 100 + "\n")
        f.write(f"{'Extension':<12} | {'Count':<6} | {'Size':<10} | {'Lines':<9} | {'Code':<9} | {'Avg Entropy':<11}\n")
        f.write("-" * 100 + "\n")
        
        sorted_exts = sorted(report.files_by_extension.items(), key=lambda x: len(x[1]), reverse=True)
        
        for ext, metrics_list in sorted_exts:
            count = len(metrics_list)
            total_size = sum(m.size_bytes for m in metrics_list)
            total_lines = sum(m.line_count for m in metrics_list)
            total_code = sum(m.code_lines for m in metrics_list)
            avg_entropy = sum(m.entropy for m in metrics_list) / count
            
            f.write(f"{ext:<12} | {count:<6} | {format_bytes(total_size):<10} | {total_lines:<9} | {total_code:<9} | {avg_entropy:.4f}\n")
        f.write("\n")

        f.write("3. CODE HEALTH INDICATORS\n")
        f.write("-" * 40 + "\n")
        f.write("Indentation Styles Found (Files):\n")
        for style, count in report.indentation_stats.most_common():
            f.write(f"  - {style}: {count}\n")
        
        f.write("\nDirectory Depth Distribution:\n")
        for depth, count in sorted(report.files_by_depth.items()):
            bar = "#" * min(count, 20)
            f.write(f"  Level {depth}: {count:<4} {bar}\n")
        f.write("\n")

        f.write("4. EXTREMES & ANOMALIES\n")
        f.write("-" * 40 + "\n")
        if report.largest_file:
            f.write(f"Largest File:           {report.largest_file.path} ({format_bytes(report.largest_file.size_bytes)})\n")
        if report.highest_entropy_file:
            f.write(f"Highest Entropy:        {report.highest_entropy_file.path} ({report.highest_entropy_file.entropy:.4f})\n")
            f.write("    (High entropy > 7.5 often indicates compressed data, encryption, or packed code)\n")
        if report.oldest_file:
            dt = datetime.datetime.fromtimestamp(report.oldest_file.created_at)
            f.write(f"Oldest File:            {report.oldest_file.path} ({dt})\n")
        if report.newest_file:
            dt = datetime.datetime.fromtimestamp(report.newest_file.modified_at)
            f.write(f"Newest File:            {report.newest_file.path} ({dt})\n")

        f.write("\n" + "="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")

    print(f"Analysis Complete. Report saved to: {os.path.abspath(output_path)}")

def main():
    report = walk_and_analyze(TARGET_PATH, SKIP_DIRS)
    write_report(report, OUTPUT_FILE)

if __name__ == "__main__":
    main()