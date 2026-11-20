import json, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote_plus
import requests
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArabicTrendFactory/1.0)"}

def shape_ar(text):
    return get_display(arabic_reshaper.reshape(str(text)))

def google_trends_sa():
    url = "https://trends.google.com/trending/rss?geo=SA"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    result = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if title:
            result.append({
                "title": title,
                "traffic": (item.findtext("approx_traffic") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
                "url": (item.findtext("link") or "").strip()
            })
    return result

def youtube_search_rss(query):
    url = "https://www.youtube.com/feeds/videos.xml?search_query=" + quote_plus(query)
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    videos = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        link = entry.find("a:link", ns)
        videos.append((title, link.attrib.get("href", "") if link is not None else ""))
    return videos[:5]

def make_script(topic):
    return [
        "موضوع اليوم: " + topic,
        "ما الذي نعرفه عن هذا الموضوع؟",
        "نراجع المعلومات من المصادر قبل الحكم.",
        "تابع التفاصيل من الروابط المرفقة.",
        "ما رأيك؟ شاركنا في التعليقات."
    ]

def font(size):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, size) if Path(p).exists() else ImageFont.load_default()

def render(topic, lines):
    w, h = int(CFG["width"]), int(CFG["height"])
    im = Image.new("RGB", (w, h), (18, 28, 48))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((55, 180, w-55, 390), radius=30, fill=(35, 63, 99))
    d.text((w-85, 245), shape_ar("ترند السعودية"), font=font(62), fill="white", anchor="ra")
    y = 500
    for line in lines:
        for start in range(0, len(line), 23):
            d.text((w-85, y), shape_ar(line[start:start+23]), font=font(47),
                   fill=(245, 248, 255), anchor="ra")
            y += 105
        y += 30
    d.text((w-85, h-170), shape_ar("Arabic Trend Factory"), font=font(42),
           fill=(160, 195, 235), anchor="ra")
    png, mp4 = OUT/"daily_video.png", OUT/"daily_video.mp4"
    im.save(png)
    subprocess.run(["ffmpeg","-y","-loop","1","-i",str(png),"-t",str(CFG["video_seconds"]),
                    "-vf",f"scale={w}:{h},format=yuv420p","-r","30","-c:v","libx264",
                    "-pix_fmt","yuv420p",str(mp4)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def main():
    trends = google_trends_sa()
    if not trends:
        raise RuntimeError("لم تصل بيانات حقيقية من Google Trends؛ لن يتم إنشاء بيانات بديلة.")
    chosen = trends[0]
    topic = chosen["title"]
    script = make_script(topic)
    render(topic, script)
    try:
        videos = youtube_search_rss(topic)
    except Exception as e:
        videos = []
        print("تعذر جلب نتائج YouTube:", e)
    report = [
        "مصدر الموضوع: Google Trends RSS — السعودية",
        "الموضوع: " + topic,
        "حجم البحث التقريبي: " + (chosen["traffic"] or "غير متاح"),
        "تاريخ المصدر: " + (chosen["published"] or "غير متاح"),
        "رابط المصدر: " + chosen["url"],
        "",
        "نتائج YouTube العامة المرتبطة بالموضوع (ليست ترتيب ترند رسمي):"
    ]
    report += [f"- {t} | {u}" for t,u in videos]
    (OUT/"trend_report.txt").write_text("\n".join(report), encoding="utf-8")
    (OUT/"daily_script.txt").write_text("\n".join(script), encoding="utf-8")
    print("تم إنشاء الفيديو والتقرير اعتمادًا على موضوع حقيقي من Google Trends.")

if __name__ == "__main__":
    main()
