# Arabic Trend Factory — النسخة الأولية

مشروع تجريبي لتجهيز فكرة وسيناريو عربي يومي اعتمادًا على بيانات YouTube المتاحة وملف CSV يدوي للترندات الأخرى.

## المتطلبات
- Python 3.10+
- FFmpeg
- مفتاح YouTube Data API اختياري

## التشغيل المحلي
```bash
pip install -r requirements.txt
python app.py
```

إذا توفر مفتاح YouTube API، أضفه في متغير البيئة `YOUTUBE_API_KEY`.

## إعداد GitHub من التابلت
1. أنشئ مستودعًا جديدًا على GitHub.
2. ارفع محتويات هذا المجلد إلى جذر المستودع، مع مجلد `.github`.
3. من Settings > Secrets and variables > Actions أضف secret باسم `YOUTUBE_API_KEY` (اختياري).
4. افتح تبويب Actions وشغّل workflow يدويًا أو انتظر موعد الجدولة.
5. نزّل Artifact باسم `daily-trend-output` من تشغيل الـ workflow.

## حدود النسخة الحالية
- يجلب بيانات YouTube الأكثر رواجًا عند توفير API key.
- TikTok وInstagram يُغذيان حاليًا عبر `data/manual_trends.csv` يدويًا؛ لا يوجد سحب تلقائي منهما.
- ينشئ فيديو عموديًا بسيطًا بخلفية ثابتة ونص عربي، وليس فيديو AI سينمائيًا.
- لا يوجد صوت أو نشر تلقائي على المنصات في هذه النسخة.
- الجدولة السحابية تعتمد على GitHub Actions وحدود الاستخدام المجانية المتاحة للحساب والمستودع.
