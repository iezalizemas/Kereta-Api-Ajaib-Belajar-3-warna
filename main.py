"""AI Kids Video Studio - Kereta Api Ajaib. Jalankan: uvicorn main:app --reload"""
import json, re, uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BASE = Path(__file__).parent
DB = BASE / "data" / "projects.json"
SET = BASE / "data" / "settings.json"
app = FastAPI(title="AI Kids Video Studio")

CHARS = {
 "Captain Choo": {"peranan": "Watak utama, kereta api mainan ajaib",
  "rupa": "cute magical toy train, bright red main body, bright blue secondary colour, gold details and a golden star, blue conductor cap with a gold star, large expressive eyes, friendly smiling face",
  "sifat": "Ceria, bijak, baik hati dan suka membantu"},
 "Momo": {"peranan": "Membantu kanak-kanak belajar warna",
  "rupa": "cute orange and white cat, large expressive eyes", "sifat": "Bijak dan ingin tahu"},
 "Rex": {"peranan": "Membantu kanak-kanak belajar nombor",
  "rupa": "cute brown and white puppy, large expressive eyes", "sifat": "Setia, suka bermain dan bertenaga"},
 "Lily": {"peranan": "Membantu kanak-kanak belajar bentuk",
  "rupa": "cute white rabbit, pink outfit and pink flower accessory, large expressive eyes", "sifat": "Mesra dan penyayang"},
 "Owlbert": {"peranan": "Memberi soalan pendidikan mudah",
  "rupa": "cute brown owl, round glasses and teacher-style cap, large expressive eyes", "sifat": "Bijak dan kelakar"},
}
STYLE = ("high-quality 3D cartoon animation, bright vibrant soft colours, cute preschool-friendly proportions, "
         "magical fantasy environment, warm lighting, cheerful positive atmosphere, vertical 9:16")
HELPER = {"Warna": "Momo", "Nombor": "Rex", "Bentuk": "Lily"}
STATUSES = ["draf", "menunggu", "diluluskan", "diterbitkan"]

def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def save(p, data):
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def make_script(p: dict) -> dict:
    names = [c for c in p.get("watak", []) if c in CHARS] or ["Captain Choo"]
    if "Captain Choo" not in names: names.insert(0, "Captain Choo")
    kat = p.get("kategori", "Warna")
    helper = next((n for n in names if n == HELPER.get(kat)), names[1] if len(names) > 1 else "Captain Choo")
    items = [x.strip() for x in re.split(r",|\bdan\b", p.get("topik", "")) if x.strip()] or [p.get("topik", "")]
    senarai = ", ".join(items[:-1]) + (" dan " if len(items) > 1 else "") + items[-1]
    msg = p.get("mesej") or f"Belajar {senarai} itu menyeronokkan!"
    dlg = [("Captain Choo", f"Hari ini kita belajar tentang {senarai}!")]
    for i in items:
        dlg.append((helper, f"Lihat! Ini {i}. Boleh tunjuk {i}?"))
        dlg.append(("Captain Choo", f"Bagus! Itu {i}. Kita sebut sama-sama: {i}!"))
    if "Owlbert" in names:
        dlg.append(("Owlbert", f"Hu-hu! Soalan untuk adik: yang manakah {items[0]}?"))
    n = {30: 4, 45: 5, 60: 6}.get(int(p.get("tempoh", 45)), 5)
    cerita = (f"Kereta api ajaib Captain Choo berlepas ke Stesen Pelangi. Di sepanjang jalan, "
              f"{helper} menunjukkan {senarai}. Semua kawan gembira kerana belajar sesuatu yang baru.")
    teks = {
      "salam": "Selamat datang, adik-adik! Saya Captain Choo! Toot-toot! Jom naik kereta api ajaib!",
      "cerita": cerita,
      "dialog": [{"watak": w, "teks": t} for w, t in dlg],
      "penerangan": f"{senarai} ialah pelajaran {kat.lower()} hari ini. {msg}",
      "misi": f"Misi kecil: Cari {items[0]} di sekeliling rumah dan tunjuk kepada ibu atau ayah!",
      "penutup": "Hebat, adik-adik! Jumpa lagi di stesen seterusnya. Toot-toot, selamat tinggal!",
    }
    fixed = ["Captain Choo menyambut penonton di stesen ajaib"] + \
            [f"{helper} dan Captain Choo mengajar: {i}" for i in items] + \
            ["Misi kecil dan soalan untuk penonton", "Captain Choo melambai selamat tinggal"]
    adegan = fixed[:n - 1] + [fixed[-1]]
    desc = "; ".join(f"{k}: {CHARS[k]['rupa']}" for k in names[:3])
    teks["adegan"] = [{"no": i + 1, "huraian": a,
        "prompt_imej": f"{a}. Characters - {desc}. Style: {STYLE}. Keep every character's appearance, colours and accessories identical to the character guide."}
        for i, a in enumerate(adegan)]
    return teks

@app.get("/")
def index(): return FileResponse(BASE / "static" / "index.html")

@app.get("/api/characters")
def characters(): return CHARS

@app.get("/api/settings")
def get_settings(): return load(SET, {"saluran": "", "bahasa": "Bahasa Melayu", "hashtag": "#KeretaApiAjaib #BelajarBersama"})
@app.put("/api/settings")
def put_settings(d: dict): save(SET, d); return d

@app.get("/api/projects")
def list_projects(): return load(DB, [])

@app.post("/api/projects")
def create(d: dict):
    ps = load(DB, [])
    d.update(id=uuid.uuid4().hex[:8], status="draf", dicipta=datetime.now().isoformat(timespec="minutes"))
    d["skrip"] = make_script(d)
    ps.append(d); save(DB, ps); return d

def find(ps, pid):
    for p in ps:
        if p["id"] == pid: return p
    raise HTTPException(404, "Projek tidak ditemui")

@app.post("/api/projects/{pid}/skrip")
def regenerate(pid: str):
    ps = load(DB, []); p = find(ps, pid)
    p["skrip"] = make_script(p); save(DB, ps); return p

@app.put("/api/projects/{pid}/skrip")
def edit_script(pid: str, d: dict):
    ps = load(DB, []); p = find(ps, pid)
    if p["status"] in ("diluluskan", "diterbitkan"): raise HTTPException(400, "Skrip yang diluluskan tidak boleh diubah")
    p["skrip"] = d; save(DB, ps); return p

@app.post("/api/projects/{pid}/status/{to}")
def set_status(pid: str, to: str):
    ps = load(DB, []); p = find(ps, pid)
    ok = {("draf", "menunggu"), ("menunggu", "diluluskan"), ("menunggu", "draf"),
          ("diluluskan", "diterbitkan"), ("diluluskan", "draf")}
    if (p["status"], to) not in ok: raise HTTPException(400, "Peralihan status tidak dibenarkan")
    p["status"] = to; save(DB, ps); return p

@app.delete("/api/projects/{pid}")
def delete(pid: str):
    save(DB, [p for p in load(DB, []) if p["id"] != pid]); return {"ok": True}
