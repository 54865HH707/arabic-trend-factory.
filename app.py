CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))

W, H = 720, 1280
OUTPUT_W = int(CONFIG["width"])
OUTPUT_H = int(CONFIG["height"])
FPS = 24
SCENES = 6

MIN_SECONDS = int(CONFIG["min_seconds"])
MAX_SECONDS = int(CONFIG["max_seconds"])
TOTAL_SECONDS = random.randint(MIN_SECONDS, MAX_SECONDS)
SCENE_SECONDS = TOTAL_SECONDS / SCENES
