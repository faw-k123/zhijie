# -*- coding: utf-8 -*-
"""为每个子类选 top5 未入库歌曲, 生成插入 SQL."""
import os, re, json, random
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"D:\评论 - 副本 (2)")
DB_SQL = Path(r"d:\zhijieguoyin_backend - 副本 - 副本\db\dbo2.sql")
OUT_SQL = Path(r"d:\zhijieguoyin_backend - 副本 - 副本\db\插入新歌曲评论_每子类top5.sql")

TOP_N_PER_SUB = 5
COMMENTS_PER_SONG = 100

random.seed(20261023)

# 1) 解析 dbo2.sql 取已有 traditional_song (title, category_id) 和 music_category
sql_text = DB_SQL.read_text(encoding="utf-8", errors="ignore")
pat_song = re.compile(r"INSERT INTO \[dbo\]\.\[traditional_song\].*?VALUES \(N'(\d+)', N'((?:[^']|'')*?)', N'(\d+)'")
existing_pairs = set()
max_song_id = 0
for m in pat_song.finditer(sql_text):
    sid = int(m.group(1))
    title = m.group(2).replace("''", "'")
    cid = int(m.group(3))
    existing_pairs.add((title, cid))
    if sid > max_song_id:
        max_song_id = sid

pat_cat = re.compile(r"INSERT INTO \[dbo\]\.\[music_category\].*?VALUES \(N'(\d+)', N'((?:[^']|'')*?)', N'((?:[^']|'')*?)'")
cat_map = {}
for m in pat_cat.finditer(sql_text):
    cid = int(m.group(1))
    parent = m.group(2)
    name = m.group(3)
    cat_map[cid] = (parent, name)
sub2cid = {name: cid for cid, (p, name) in cat_map.items()}

print(f"existing songs: {len(existing_pairs)}, max_song_id={max_song_id}")
print(f"categories: {len(cat_map)}")

# 2) 扫描评论文件夹
def detect_platform(fp: Path) -> str:
    name = fp.name.lower()
    parent = fp.parent.name.lower()
    grand = fp.parent.parent.name.lower() if fp.parent.parent else ""
    for s in (name, parent, grand):
        if "netease" in s or "网易云" in s or "wangyiyun" in s or "wangyi" in s:
            return "netease"
        if "bilibili" in s or "b站" in s or "bzhan" in s:
            return "bilibili"
        if "youtube" in s or "油管" in s:
            return "youtube"
    return "unknown"

def collect_song_comments(song_dir: Path):
    """返回 [(source, content, likes)]"""
    rows = []
    for fp in song_dir.rglob("*.jsonl"):
        if "翻译" in fp.name or "translate" in fp.name.lower():
            continue
        plat = detect_platform(fp)
        if plat == "unknown":
            continue
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    content = (obj.get("评论内容") or "").strip()
                    if not content:
                        continue
                    likes = obj.get("点赞数", 0)
                    try:
                        likes = int(likes)
                    except Exception:
                        likes = 0
                    rows.append((plat, content, likes))
        except Exception:
            continue
    return rows

# 3) 按 (parent, sub) 选 top5 未入库歌曲
selected = {}  # (parent, sub) -> [(song_folder, total, comments)]
top_parents = ["乐器", "民歌", "戏曲", "说唱"]
for parent in top_parents:
    p_dir = ROOT / parent
    if not p_dir.exists():
        continue
    for sub in sorted(os.listdir(p_dir)):
        sub_dir = p_dir / sub
        if not sub_dir.is_dir():
            continue
        cand = None
        for sub_folder_name in ["其他", "评论", "歌曲"]:
            cand_dir = sub_dir / sub_folder_name
            if cand_dir.exists():
                cand = cand_dir
                break
        if cand is None:
            # 没有中间层, 直接用 sub_dir (如 戏曲/黄梅/<歌曲>/...)
            cand = sub_dir
        cid = sub2cid.get(sub)
        if cid is None:
            continue
        rows = []
        for song_folder in sorted(os.listdir(cand)):
            if song_folder.endswith("__2"):
                continue
            song_dir = cand / song_folder
            if not song_dir.is_dir():
                continue
            comments = collect_song_comments(song_dir)
            if not comments:
                continue
            rows.append((song_folder, len(comments), comments))
        # 排序: 按评论数降序
        rows.sort(key=lambda x: -x[1])
        # 过滤已入库
        fresh = [r for r in rows if (r[0], cid) not in existing_pairs]
        selected[(parent, sub, cid)] = fresh[:TOP_N_PER_SUB]

# 4) 生成 SQL
def sql_escape(s: str) -> str:
    return s.replace("'", "''")

def trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n]

# 随机日期
from datetime import date, timedelta
START = date(2024, 1, 1)
END = date(2026, 9, 15)
DAYS = (END - START).days
def rand_date():
    return START + timedelta(days=random.randint(0, DAYS))

lines = []
lines.append("-- 为每个子类插入 top5 首未入库歌曲及其 top100 评论 (按点赞降序)")
lines.append("-- traditional_song 与 comment 都使用 NOT EXISTS 去重")
lines.append("")
lines.append("USE [music_db_test];")
lines.append("GO")
lines.append("")

# ------- traditional_song -------
lines.append("-- ===== 新歌曲 =====")
lines.append("IF OBJECT_ID('tempdb..#newsong') IS NOT NULL DROP TABLE #newsong;")
lines.append("GO")
lines.append("CREATE TABLE #newsong (")
lines.append("  [title] nvarchar(200) NOT NULL,")
lines.append("  [category_id] int NOT NULL,")
lines.append("  [genre] nvarchar(100) NOT NULL,")
lines.append("  [audio_url] nvarchar(500) NOT NULL,")
lines.append("  [cover_url] nvarchar(500) NOT NULL")
lines.append(");")
lines.append("GO")
lines.append("")

new_songs_rows = []  # (title, cid, genre, audio_url, cover_url)
song_key_to_idx = {}
for (parent, sub, cid), songs in selected.items():
    if not songs:
        continue
    for song_folder, total, comments in songs:
        title = song_folder
        audio_url = f"audio/{parent}/{sub}/{song_folder}.mp3"
        cover_url = f"images/poster/{parent}/{sub}.jpg"
        key = (title, cid)
        if key in song_key_to_idx:
            continue
        song_key_to_idx[key] = len(new_songs_rows)
        new_songs_rows.append((title, cid, sub, audio_url, cover_url))

BATCH = 500
for i in range(0, len(new_songs_rows), BATCH):
    chunk = new_songs_rows[i:i+BATCH]
    lines.append("INSERT INTO #newsong ([title],[category_id],[genre],[audio_url],[cover_url]) VALUES")
    vals = []
    for title, cid, genre, audio_url, cover_url in chunk:
        vals.append(f"(N'{sql_escape(trunc(title,190))}', N'{cid}', N'{sql_escape(trunc(genre,90))}', N'{sql_escape(trunc(audio_url,490))}', N'{sql_escape(trunc(cover_url,490))}')")
    lines.append(",\n".join(vals) + ";")
    lines.append("GO")
lines.append("")

lines.append("DECLARE @song_base int = (SELECT ISNULL(MAX([id]),0) FROM [dbo].[traditional_song]);")
lines.append(";WITH new_songs AS (")
lines.append("  SELECT n.*, ROW_NUMBER() OVER (ORDER BY n.[category_id], n.[title]) AS rn")
lines.append("  FROM #newsong n")
lines.append("  WHERE NOT EXISTS (")
lines.append("    SELECT 1 FROM [dbo].[traditional_song] t")
lines.append("    WHERE t.[title] = n.[title] AND t.[category_id] = n.[category_id]")
lines.append("  )")
lines.append(")")
lines.append("INSERT INTO [dbo].[traditional_song] ([id],[title],[category_id],[genre],[audio_url],[cover_url])")
lines.append("SELECT @song_base + rn, [title],[category_id],[genre],[audio_url],[cover_url]")
lines.append("FROM new_songs;")
lines.append("GO")
lines.append("")
lines.append("DROP TABLE #newsong;")
lines.append("GO")
lines.append("")

# ------- comment -------
lines.append("-- ===== 新评论 =====")
lines.append("IF OBJECT_ID('tempdb..#newcmt') IS NOT NULL DROP TABLE #newcmt;")
lines.append("GO")
lines.append("CREATE TABLE #newcmt (")
lines.append("  [song_title] nvarchar(200) NOT NULL,")
lines.append("  [category_id] int NOT NULL,")
lines.append("  [source] nvarchar(50) NOT NULL,")
lines.append("  [content] nvarchar(4000) NOT NULL,")
lines.append("  [likes] int NULL,")
lines.append("  [comment_time] date NULL")
lines.append(");")
lines.append("GO")
lines.append("")

new_cmt_rows = []  # (song_title, cid, source, content, likes, comment_time)
summary_stats = []
for (parent, sub, cid), songs in selected.items():
    if not songs:
        continue
    for song_folder, total, comments in songs:
        title = song_folder
        # 按点赞降序, 取前100
        comments_sorted = sorted(comments, key=lambda x: -x[2])
        top_comments = comments_sorted[:COMMENTS_PER_SONG]
        # 同歌曲内去重 (source+content)
        seen = set()
        kept = []
        for plat, content, likes in top_comments:
            k = (plat, content)
            if k in seen:
                continue
            seen.add(k)
            kept.append((plat, content, likes))
        summary_stats.append((parent, sub, cid, title, total, len(kept)))
        for plat, content, likes in kept:
            d = rand_date().isoformat()
            new_cmt_rows.append((title, cid, plat, content, likes, d))

print(f"total new songs rows: {len(new_songs_rows)}")
print(f"total new comment rows: {len(new_cmt_rows)}")

BATCH = 500
for i in range(0, len(new_cmt_rows), BATCH):
    chunk = new_cmt_rows[i:i+BATCH]
    lines.append("INSERT INTO #newcmt ([song_title],[category_id],[source],[content],[likes],[comment_time]) VALUES")
    vals = []
    for title, cid, src, content, likes, d in chunk:
        vals.append(f"(N'{sql_escape(trunc(title,190))}', N'{cid}', N'{src}', N'{sql_escape(trunc(content,3900))}', N'{likes}', N'{d}')")
    lines.append(",\n".join(vals) + ";")
    lines.append("GO")
lines.append("")

lines.append("DECLARE @cmt_base int = (SELECT ISNULL(MAX([id]),0) FROM [dbo].[comment]);")
lines.append(";WITH cmt_with_sid AS (")
lines.append("  SELECT t.[id] AS song_id, n.[source], n.[content], n.[likes], n.[comment_time]")
lines.append("  FROM #newcmt n")
lines.append("  JOIN [dbo].[traditional_song] t")
lines.append("    ON t.[title] = n.[song_title] AND t.[category_id] = n.[category_id]")
lines.append(")")
lines.append("INSERT INTO [dbo].[comment] ([id],[song_id],[content],[likes],[source],[comment_time])")
lines.append("SELECT @cmt_base + ROW_NUMBER() OVER (ORDER BY song_id, [source], [content]),")
lines.append("       song_id, [content], [likes], [source], [comment_time]")
lines.append("FROM cmt_with_sid c")
lines.append("WHERE NOT EXISTS (")
lines.append("  SELECT 1 FROM [dbo].[comment] x")
lines.append("  WHERE x.[song_id]=c.[song_id] AND x.[source]=c.[source] AND x.[content]=c.[content]")
lines.append(");")
lines.append("GO")
lines.append("")
lines.append("DROP TABLE #newcmt;")
lines.append("GO")

OUT_SQL.write_text("\n".join(lines), encoding="utf-8")
print(f"written -> {OUT_SQL}")
print(f"size = {OUT_SQL.stat().st_size:,} bytes")

# 输出每个子类的选择摘要
print("\n===== 选择摘要 =====")
for (parent, sub, cid), songs in selected.items():
    if not songs:
        print(f"{parent}/{sub} (cid={cid}): 无新歌")
        continue
    print(f"{parent}/{sub} (cid={cid}): 选 {len(songs)} 首")
    for song_folder, total, comments in songs:
        print(f"   {song_folder}  (总评论 {total})")
