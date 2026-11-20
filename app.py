import json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, random, hashlib, subprocess, shutil, csv, re, html
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; AS=OUT/"assets"; OUT.mkdir(exist_ok=True); AS.mkdir(exist_ok=True)
D={"country_code":"SA","min_seconds":60,"max_seconds":90,"width":1080,"height":1920,"voice":"ar-SA-HamedNeural","allow_web_images":True}
try: D.update(json.loads((ROOT/"config.json").read_text(encoding="utf-8")))
except: pass

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ArabicTrendFactory/2.0"})
    return urllib.request.urlopen(req,timeout=22).read()

def trends():
    try:
        x=ET.fromstring(get("https://trends.google.com/trending/rss?geo="+D["country_code"]))
        return [i.findtext("title","").strip() for i in x.findall(".//item") if i.findtext("title")][:12]
    except Exception as e:
        print("Trends RSS unavailable:",e); return []

FORMATS={
"كرتون ومواقف":["تخيل لو صار موقف يومي بسيط كارثة كوميدية؟","الشخصية تحاول تحل المشكلة، لكن كل حل يسبب مشكلة أكبر.","وفي النهاية تكتشف أن أبسط حل كان أمامها من البداية."],
"حقائق غريبة":["فيه أشياء حولنا تبدو عادية، لكن وراءها تفاصيل مدهشة.","كل ما نحتاجه هو الفضول والسؤال والبحث عن تفسير موثوق.","لا تنقل أي معلومة قبل التأكد من مصدرها."],
"غموض":["في ليلة هادئة، ظهر شيء لم يكن موجودًا قبل دقائق.","حاول البطل تفسير ما حدث، لكن كل دليل فتح سؤالًا جديدًا.","وفي اللحظة الأخيرة ظهرت تفصيلة قلبت القصة."],
"ألغاز وتحديات":["اختبر تركيزك: لا تستعجل بالإجابة.","خذ لحظة، وراجع التفاصيل مرة ثانية.","هل وصلت للحل؟ اكتب إجابتك قبل قراءة التعليقات."],
"عشوائيات":["تخيل لو اختفى الشيء هذا لمدة دقيقة واحدة؟","كيف سيتغير يومنا؟ وما أول مشكلة سنواجهها؟","أحيانًا سؤال غريب يفتح نقاشًا ممتعًا."],
"قصة قصيرة":["كان يعتقد أن يومه عادي تمامًا، إلى أن حدث شيء غير متوقع.","قرار صغير قاده إلى سلسلة أحداث لم يتخيلها.","لكن النهاية كانت مختلفة تمامًا عما توقع."]
}
def category(day):
    keys=list(FORMATS); seed=int(hashlib.sha256(day.encode()).hexdigest()[:8],16)
    random.Random(seed).shuffle(keys); return keys[seed%len(keys)]
def commons(q):
    if not D.get("allow_web_images",True): return []
    u="https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch="+urllib.parse.quote(q)+"&gsrnamespace=6&gsrlimit=12&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1000&format=json"
    try:
        pages=list(json.loads(get(u)).get("query",{}).get("pages",{}).values()); random.shuffle(pages); out=[]
        for p in pages:
            ii=(p.get("imageinfo") or [{}])[0]; url=ii.get("thumburl") or ii.get("url")
            if not url or not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)",url,re.I): continue
            m=ii.get("extmetadata",{})
            clean=lambda k: re.sub("<.*?>","",html.unescape(m.get(k,{}).get("value","")))
            out.append((url,p.get("title",""),clean("LicenseShortName"),clean("Artist"),ii.get("descriptionurl","")))
            if len(out)==6: break
        return out
    except Exception as e: print("Commons unavailable:",e); return []
def cmd(a): subprocess.run(a,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def image_card(path,i,text):
    from PIL import Image,ImageDraw,ImageFont
    w,h=D["width"],D["height"]; colors=[(17,32,72),(26,74,83),(78,39,75),(34,57,98)]
    c=colors[i%len(colors)]; im=Image.new("RGB",(w,h),c); d=ImageDraw.Draw(im)
    for k in range(9):
        x=(k*173+i*71)%w; y=(k*257+i*111)%h
        d.ellipse((x-130,y-130,x+130,y+130),outline=(110,160,210),width=7)
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",55)
    except: f=ImageFont.load_default()
    d.rounded_rectangle((45,int(h*.68),w-45,int(h*.91)),radius=35,fill=(5,10,25))
    d.text((w//2,int(h*.80)),text[:75],font=f,fill="white",anchor="mm",align="center",direction="rtl")
    im.save(path,quality=90)
def main():
    day=datetime.now(timezone.utc).date().isoformat(); trends_list=trends(); cat=category(day)
    trend=trends_list[0] if trends_list and cat in ("حقائق غريبة","عشوائيات","قصة قصيرة") else None
    topic=trend or random.choice({"كرتون ومواقف":["مواقف يومية مضحكة"],"حقائق غريبة":["غرائب الطبيعة"],"غموض":["رسالة مجهولة"],"ألغاز وتحديات":["لغز الملاحظة"],"عشوائيات":["ماذا لو اختفت الجاذبية؟"],"قصة قصيرة":["قرار غيّر كل شيء"]}[cat])
    beats=[f"انتبه! {topic}",f"حلقة اليوم: {cat}.",*FORMATS[cat], "وش رأيك؟ اكتب لنا اقتراح الحلقة القادمة."]
    # Exactly six scene cards
    beats=(beats+beats)[:6]
    imgs=commons(topic+" "+("illustration" if cat in ("كرتون ومواقف","غموض","قصة قصيرة") else "photo"))
    credits=[]; clips=[]; per=max(10,min(15,int(D["max_seconds"])//6))
    for i,txt in enumerate(beats):
        src=AS/f"source_{i}.jpg"; used=False
        if imgs:
            item=imgs[i%len(imgs)]
            try: src.write_bytes(get(item[0])); used=src.stat().st_size>3000
            except: used=False
            if used: credits.append([src.name,*item[1:]])
        if not used: image_card(src,i,txt)
        from PIL import Image,ImageDraw,ImageFont
        im=Image.open(src).convert("RGB").resize((D["width"],D["height"]))
        d=ImageDraw.Draw(im,"RGBA"); d.rectangle((0,int(D["height"]*.70),D["width"],D["height"]),fill=(0,0,0,165))
        try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",50)
        except: f=ImageFont.load_default()
        d.text((D["width"]//2,int(D["height"]*.82)),txt[:90],font=f,fill="white",anchor="mm",align="center",direction="rtl")
        frame=AS/f"scene_{i}.jpg"; im.save(frame,quality=92)
        clip=AS/f"clip_{i}.mp4"; frames=per*25
        vf=f"scale={D['width']}:{D['height']}:force_original_aspect_ratio=increase,crop={D['width']}:{D['height']},zoompan=z='min(zoom+0.0008,1.08)':d={frames}:s={D['width']}x{D['height']}:fps=25,format=yuv420p"
        cmd(["ffmpeg","-y","-loop","1","-i",str(frame),"-vf",vf,"-t",str(per),"-r","25","-an","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(clip)])
        clips.append(clip)
    con=AS/"concat.txt"; con.write_text("".join(f"file '{p.resolve()}'\n" for p in clips))
    silent=OUT/"silent.mp4"; cmd(["ffmpeg","-y","-f","concat","-safe","0","-i",str(con),"-c","copy",str(silent)])
    voice=OUT/"voice.mp3"; voice_ok=False
    script=" ".join(beats)
    try:
        cmd(["python","-m","edge_tts","--voice",D["voice"],"--text",script,"--write-media",str(voice)])
        voice_ok=voice.exists() and voice.stat().st_size>1000
    except Exception as e: print("TTS unavailable; silent video fallback:",e)
    final=OUT/"arabic_daily_video.mp4"
    if voice_ok: cmd(["ffmpeg","-y","-i",str(silent),"-i",str(voice),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest",str(final)])
    else: shutil.copyfile(silent,final)
    (OUT/"daily_script.txt").write_text("\n\n".join(beats),encoding="utf-8")
    with (OUT/"image_credits.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["File","Title","License","Author","Source"]); w.writerows(credits)
    (OUT/"trend_report.txt").write_text(f"التاريخ: {day}\nالنوع: {cat}\nالموضوع: {topic}\nعناصر Trends المتاحة: {len(trends_list)}\nصور Commons: {len(credits)}\nالصوت: {'تم إنشاؤه' if voice_ok else 'غير متاح في هذا التشغيل'}\nالفيديو: {final.name}\nتنبيه: السيناريو قالب ترفيهي وليس تحققًا صحفيًا من الحقائق.",encoding="utf-8")
    print("Generated",final)
if __name__=="__main__": main()
