import os, math, random, subprocess, asyncio, shutil, json, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("output")
ASSETS = OUT / "assets"
W, H = 720, 1280
FPS = 24
SCENE_SECONDS = 12
SCENES = 6
TOTAL_SECONDS = SCENE_SECONDS * SCENES

def run(cmd):
    subprocess.run(cmd, check=True)

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def shape_ar(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def draw_center(draw, text, y, fnt, fill, max_width=650):
    s = shape_ar(text)
    # wrap by words to fit width
    words = s.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0,0), trial, font=fnt)[2] <= max_width:
            line = trial
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    for ln in lines[:3]:
        box = draw.textbbox((0,0), ln, font=fnt, stroke_width=1)
        x = (W - (box[2]-box[0])) // 2
        draw.text((x, y), ln, font=fnt, fill=fill, stroke_width=2, stroke_fill=(20,20,35))
        y += fnt.size + 12
    return y

# Each scene is a different illustrated setting. Character/object positions vary by scene.
PALETTES = [
    ((18,32,76),(56,120,180),(255,196,75)),
    ((35,18,65),(115,63,145),(255,130,115)),
    ((10,65,75),(34,145,130),(255,220,110)),
    ((50,28,20),(170,92,50),(255,190,90)),
    ((22,42,80),(62,95,160),(180,220,255)),
    ((45,22,55),(130,65,110),(255,190,220)),
]
TITLES = [
    "بداية الحكاية", "شيء غير متوقع", "لحظة الاكتشاف",
    "المشكلة تكبر", "الحل الذكي", "النهاية المفاجئة"
]

def draw_star(d, x, y, r, color):
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5
        rr=r if i%2==0 else r*0.42
        pts.append((x+math.cos(a)*rr,y+math.sin(a)*rr))
    d.polygon(pts, fill=color)

def draw_character(d, cx, cy, scale, shirt, skin=(255,205,160), mood=0):
    # legs
    d.line((cx-18*scale,cy+75*scale,cx-32*scale,cy+125*scale),fill=(30,35,55),width=max(5,int(12*scale)))
    d.line((cx+18*scale,cy+75*scale,cx+32*scale,cy+125*scale),fill=(30,35,55),width=max(5,int(12*scale)))
    # body
    d.rounded_rectangle((cx-48*scale,cy+5*scale,cx+48*scale,cy+95*scale),radius=int(22*scale),fill=shirt,outline=(20,25,45),width=4)
    # arms
    d.line((cx-40*scale,cy+25*scale,cx-78*scale,cy+65*scale),fill=skin,width=max(5,int(14*scale)))
    d.line((cx+40*scale,cy+25*scale,cx+78*scale,cy+65*scale),fill=skin,width=max(5,int(14*scale)))
    # head and hair
    d.ellipse((cx-48*scale,cy-85*scale,cx+48*scale,cy+12*scale),fill=skin,outline=(20,25,45),width=4)
    d.pieslice((cx-50*scale,cy-95*scale,cx+50*scale,cy-5*scale),180,360,fill=(35,25,35))
    # eyes / smile
    d.ellipse((cx-22*scale,cy-42*scale,cx-10*scale,cy-30*scale),fill=(20,25,35))
    d.ellipse((cx+10*scale,cy-42*scale,cx+22*scale,cy-30*scale),fill=(20,25,35))
    if mood % 2:
        d.arc((cx-18*scale,cy-25*scale,cx+18*scale,cy+2*scale),10,170,fill=(120,35,45),width=3)
    else:
        d.arc((cx-18*scale,cy-28*scale,cx+18*scale,cy+2*scale),5,175,fill=(120,35,45),width=3)

def make_scene(i, caption, story_title):
    top, bottom, accent = PALETTES[i]
    im=Image.new("RGB",(W,H),top)
    d=ImageDraw.Draw(im)
    # gradient bands and scene-specific scenery
    for y in range(H):
        t=y/H
        c=tuple(int(top[k]*(1-t)+bottom[k]*t) for k in range(3))
        d.line((0,y,W,y),fill=c)
    # stars / bubbles
    rng=random.Random(100+i)
    for _ in range(45):
        x=rng.randint(20,W-20); y=rng.randint(100,900); r=rng.randint(3,10)
        if i in (0,4): draw_star(d,x,y,r,accent)
        else: d.ellipse((x-r,y-r,x+r,y+r),outline=accent,width=2)
    # ground / stage varies
    if i == 0:
        d.ellipse((65,930,655,1120),fill=(40,55,90))
        draw_character(d,360,760,1.45,(255,160,70),mood=i)
        d.rounded_rectangle((475,670,635,820),radius=24,fill=(245,220,140),outline=(25,25,45),width=5)
        d.ellipse((520,705,590,775),fill=(80,140,210))
    elif i == 1:
        d.rectangle((0,930,W,H),fill=(45,35,80))
        d.rounded_rectangle((105,610,615,920),radius=50,fill=(70,80,130),outline=accent,width=8)
        d.ellipse((245,690,475,920),fill=(35,45,80),outline=accent,width=8)
        draw_character(d,360,760,1.1,(90,210,180),mood=i)
    elif i == 2:
        d.polygon([(0,950),(160,700),(300,950),(470,650),(720,950)],fill=(30,100,105))
        d.ellipse((260,600,460,800),fill=accent,outline=(255,255,255),width=5)
        draw_character(d,360,800,1.15,(255,110,120),mood=i)
    elif i == 3:
        d.rectangle((0,930,W,H),fill=(80,45,35))
        for x in (80,260,440,620):
            d.polygon([(x,930),(x+80,720),(x+160,930)],fill=(110,60,45))
        draw_character(d,360,770,1.25,(100,170,250),mood=i)
    elif i == 4:
        d.ellipse((130,650,590,1110),fill=(35,80,125),outline=accent,width=10)
        d.rounded_rectangle((245,680,475,870),radius=35,fill=(235,240,250),outline=(20,30,60),width=6)
        d.ellipse((295,730,425,860),fill=(80,190,210))
        draw_character(d,360,790,0.95,(245,150,70),mood=i)
    else:
        d.rectangle((0,930,W,H),fill=(85,35,75))
        d.ellipse((170,610,550,990),fill=(255,190,220),outline=(255,255,255),width=8)
        draw_character(d,360,760,1.2,(110,190,255),mood=i)
        draw_star(d,540,640,55,(255,240,130))
    # top label and bottom caption card
    d.rounded_rectangle((35,45,685,145),radius=28,fill=(12,18,40))
    draw_center(d,story_title,68,font(32,True),(255,255,255))
    d.rounded_rectangle((35,1010,685,1225),radius=30,fill=(12,18,40))
    draw_center(d,TITLES[i],1035,font(31,True),accent)
    draw_center(d,caption,1090,font(27,True),(255,255,255),610)
    return im

def choose_story():
    choices = [
        ("مغامرة الروبوت الصغير",
         ["في مدينة هادئة، كان روبوت صغير يحلم أن يصبح مستكشفًا.",
          "ذات ليلة، لمح ضوءًا غريبًا يخرج من صندوق قديم.",
          "اقترب بحذر، فوجد خريطة تقود إلى حديقة مخفية.",
          "لكن بوابة الحديقة أغلقت فجأة، ولم يعد يعرف طريق العودة.",
          "لاحظ رموزًا مضيئة على الأرض، فرتبها مثل قطع الأحجية.",
          "انفتحت البوابة، واكتشف أن الكنز الحقيقي هو المكان الذي صنعه بنفسه."]),
        ("سر القمر الأزرق",
         ["في ليلة صافية، لاحظت ليان أن القمر يبدو أزرق في انعكاس البحيرة.",
          "حملت مصباحها وذهبت لترى ما يحدث قرب الماء.",
          "وجدت فراشات مضيئة ترسم طريقًا بين الأشجار.",
          "فجأة اختفى الضوء، وبقيت علامة صغيرة على صخرة.",
          "اتبعت العلامة واكتشفت مرآة قديمة تعكس السماء.",
          "ضحكت ليان، فقد كان السر انعكاسًا جميلًا لا أكثر."]),
        ("المقلب الذي انقلب",
         ["قرر سامي أن يفاجئ أصدقاءه بمقلب طريف في الحديقة.",
          "خبأ صندوقًا يصدر صوتًا مضحكًا كلما اقترب أحد.",
          "اقترب أصدقاؤه بحذر، ثم بدأ الصندوق يهتز بقوة.",
          "هرب سامي من الضحك، لكنه نسي أن الصندوق مربوط بحقيبته.",
          "طار الصندوق خلفه، فظن الجميع أن هناك وحشًا صغيرًا.",
          "وفي النهاية اكتشفوا المقلب، وضحكوا جميعًا على سامي."]),
        ("رحلة إلى كوكب الألوان",
         ["انطلق رائد فضاء صغير في رحلة إلى كوكب لم يره أحد.",
          "كانت الجبال بنفسجية والأنهار تلمع مثل النجوم.",
          "قابل مخلوقًا لطيفًا لا يتكلم إلا بالأضواء.",
          "فهم أن المخلوق يبحث عن نجمة ضائعة.",
          "تعاونا وصنعا منطادًا من أوراق مضيئة للبحث عنها.",
          "عادت النجمة إلى السماء، وأصبح للكوكب حارس جديد."]),
    ]
    return random.choice(choices)

async def make_voice(text, path):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="+2%", volume="+0%")
        await communicate.save(str(path))
        return True
    except Exception as e:
        print("Arabic TTS unavailable:", repr(e))
        return False

def fetch_pixabay_videos():
    """Fetch a small set of Pixabay videos when PIXABAY_API_KEY is configured."""
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key:
        print("PIXABAY_API_KEY is not configured; using illustrated fallback scenes.")
        return []
    params = urllib.parse.urlencode({"key": key, "q": "cartoon animation", "per_page": 30, "safesearch": "true"})
    url = "https://pixabay.com/api/videos/?" + params
    req = urllib.request.Request(url, headers={"User-Agent": "ArabicTrendFactory/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
        hits = payload.get("hits", [])
        random.shuffle(hits)
        downloaded = []
        for hit in hits:
            if len(downloaded) >= SCENES:
                break
            variants = hit.get("videos", {})
            variant = variants.get("medium") or variants.get("small") or variants.get("large")
            if not variant or not variant.get("url"):
                continue
            target = ASSETS / f"pixabay_{len(downloaded)}.mp4"
            try:
                request = urllib.request.Request(variant["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(request, timeout=45) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.stat().st_size > 25_000:
                    downloaded.append((target, hit.get("pageURL", "Pixabay")))
                else:
                    target.unlink(missing_ok=True)
            except Exception as exc:
                print("Could not download Pixabay clip:", exc)
        return downloaded
    except Exception as exc:
        print("Pixabay API request failed; using illustrated fallback scenes:", repr(exc))
        return []

def make_overlay(i, caption, story_title):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((28, 38, 692, 155), radius=28, fill=(10, 16, 35, 215))
    draw_center(d, story_title, 66, font(31, True), (255,255,255,255))
    d.rounded_rectangle((28, 1000, 692, 1235), radius=30, fill=(10, 16, 35, 220))
    draw_center(d, TITLES[i], 1024, font(30, True), (255,210,100,255))
    draw_center(d, caption, 1080, font(26, True), (255,255,255,255), 610)
    return overlay

def main():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required but was not found.")
    OUT.mkdir(exist_ok=True); ASSETS.mkdir(parents=True,exist_ok=True)
    story_title, lines = choose_story()
    print("Selected:", story_title)
    for i, line in enumerate(lines):
        im=make_scene(i,line,story_title)
        im.save(ASSETS/f"scene_{i}.jpg",quality=92)
    script = " ".join(lines)
    (OUT/"daily_script.txt").write_text(story_title+"\n\n"+script,encoding="utf-8")
    audio=OUT/"voice.mp3"
    ok=asyncio.run(make_voice(script,audio))
    # Create six distinct animated scenes with gentle zoom and pan.
    segments=[]
    pixabay_clips = fetch_pixabay_videos()
    for i in range(SCENES):
        dst=ASSETS/f"clip_{i}.mp4"
        if i < len(pixabay_clips):
            video_path, source_page = pixabay_clips[i]
            overlay_path = ASSETS/f"overlay_{i}.png"
            make_overlay(i, lines[i], story_title).save(overlay_path)
            filt=f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]"
            run(["ffmpeg","-y","-stream_loop","-1","-i",str(video_path),"-i",str(overlay_path),"-filter_complex",filt,"-map","[v]","-t",str(SCENE_SECONDS),"-r",str(FPS),"-an","-c:v","libx264","-preset","veryfast","-crf","24",str(dst)])
        else:
            src=ASSETS/f"scene_{i}.jpg"
            zoom = "min(zoom+0.0012,1.12)" if i%2==0 else "if(lte(zoom,1.0),1.12,max(1.0,zoom-0.0012))"
            vf=f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={SCENE_SECONDS*FPS}:s={W}x{H}:fps={FPS},format=yuv420p"
            run(["ffmpeg","-y","-loop","1","-i",str(src),"-vf",vf,"-t",str(SCENE_SECONDS),"-r",str(FPS),"-an","-c:v","libx264","-preset","veryfast","-crf","24",str(dst)])
        segments.append(dst)
    concat=ASSETS/"concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segments),encoding="utf-8")
    silent=OUT/"silent.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    final=OUT/"arabic_daily_video.mp4"
    if ok:
        run(["ffmpeg","-y","-i",str(silent),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-af","apad","-t",str(TOTAL_SECONDS),"-c:v","copy","-c:a","aac","-b:a","128k","-shortest",str(final)])
    else:
        run(["ffmpeg","-y","-i",str(silent),"-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=44100","-map","0:v:0","-map","1:a:0","-t",str(TOTAL_SECONDS),"-c:v","copy","-c:a","aac","-shortest",str(final)])
    (OUT/"trend_report.txt").write_text(
        f"Content type: fictional animated story\nTitle: {story_title}\nScenes: {SCENES}\nTarget duration: {TOTAL_SECONDS} seconds\nArabic voice generated: {ok}\n",
        encoding="utf-8")
    print("Created:", final, "duration target:", TOTAL_SECONDS)

if __name__ == "__main__":
    main()
