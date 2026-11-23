# 测试资源目录

每个音乐资源放在独立子文件夹中（文件夹名即歌曲名），例如当前已有：

```
backend/media/resources/牡丹江/
  mv.mp4        # MV 视频
  audio.mp3     # 音频
  lyrics.lrc    # LRC 带时间轴歌词（必须用 .lrc）
  intro.txt     # 简介
```

内容展示模块会自动扫描本目录，生成：
- `/media/resources/牡丹江/mv.mp4`
- `/media/resources/牡丹江/audio.mp3`
- `/media/resources/牡丹江/lyrics.lrc`
