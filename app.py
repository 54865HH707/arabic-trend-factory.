import csv, json, os, subprocess, textwrap
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA = ROOT / "data" / "manual_trends.csv"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

def get_youtube():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part":"snippet,statistics","chart":"mostPopular","regionCode":"SA","maxResults":25,"key":key}
    try:
        items = requests.get(url, params=params, timeout=25).json().get("items", [])
        rows = []
        for item in items:
            stats = item.get("statistics", {})
            rows.append({"platform":"YouTube","title":item["snippet"]["title"],
                         "views":int(stats.get("viewCount",0)),
                         "likes":int(stats.get("likeCount",0)),
                         "comments":int(stats.get("commentCount",0)),
                         "url":"https://youtube.com/watch?v="+item["id"]})
        return rows
    except Exception as exc:
        print("YouTube fetch failed:", exc)
        return []

def get_manual():
    if not DATA.exists(): return []
    with DATA.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def score(row):
    views = int(row.get("views") or 0)
    likes = int(row.get("likes") or 0)
    comments = int(row.get("comments") or 0)
    return views + likes*20 + comments*30

def make_script(title):
    return [
        f"هل سمعت عن: {title}؟",
        "الموضوع بدأ ينتشر والناس تتكلم عنه!",
        "خلّنا نفهم الفكرة بسرعة وببساطة.",
        "وش رأيك؟ اكتب لنا في التعليقات."
    ]

def arabic(text):
    return get_display(arabic_reshaper.reshape(str(text)))

def render(title, script):
    w, h = CFG["width"], CFG["height"]
    img = Image.new("RGB", (w,h), (18, 28, 48))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try: font = ImageFont.truetype(font_path,  sixty :=  sixty if False else 58)
    except Exception: font = ImageFont.load_default()
    lines = [title] + script
    y = 430
    for line in lines:
        wrapped = textwrap.wrap(line, width=25)
        for part in wrapped:
            draw.text((w-70,y), arabic(part), font=font, fill=(255,255,255), anchor="ra")
            y += 105
        y += 35
    draw.text((w-70,h-160), arabic("Arabic Trend Factory"), font=font, fill=(180,210,255), anchor="ra")
    png = OUT / "daily_video.png"
    img.save(png)
    mp4 = OUT / "daily_video.mp4"
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(png),"-t",str(CFG["video_seconds"]),
                    "-vf",f"scale={w}:{h},format=yuv420p","-r","30","-c:v","libx264","-pix_fmt","yuv420p",str(mp4)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp4

def main():
    trends = get_youtube() + get_manual()
    if not trends:
        trends = [{"platform":"Demo","title":"أضف بيانات ترند حقيقية في ملف CSV","views":0,"likes":0,"comments":0}]
    best = max(trends, key=score)
    title = str(best.get("title","فكرة اليوم"))
    script = make_script(title)
    (OUT/"daily_script.txt").write_text("\\n".join(script), encoding="utf-8")
    (OUT/"selected_trend.txt").write_text(f"{best.get('platform')} | {title}\\nScore: {score(best)}", encoding="utf-8")
    render(title, script)
    print("Created output files in", OUT)

if __name__ == "__main__":
    main()
