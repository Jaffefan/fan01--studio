"""GitHub Pages 发布模块：在当前 git 仓库内组织内容并 push"""

import sys
import os
import json
import shutil
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import GITHUB_PAGES_URL


def publish(site_dir: str, episode_id: str, script: dict | None = None, chapters: list | None = None) -> str:
    """
    发布本期到当前仓库的 episodes/{episode_id}/，重建归档首页，commit + push。
    本地和 GitHub Actions 共用同一逻辑（都在当前 git 仓库内操作）。
    """
    repo_dir = "."  # 当前目录就是 git 仓库

    # 1. 复制本期到 episodes/<episode_id>/
    episode_dir = os.path.join(repo_dir, "episodes", episode_id)
    if os.path.exists(episode_dir):
        shutil.rmtree(episode_dir)
    shutil.copytree(site_dir, episode_dir)

    # 2. 保存本期 metadata
    if script is not None:
        meta = _build_episode_meta(episode_id, script, chapters or [])
        meta_path = os.path.join(episode_dir, "episode_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    # 3. 重建归档首页
    from archive_generator import build_archive
    build_archive(repo_dir)

    # 4. .nojekyll 让 Pages 不走 Jekyll 解析
    nojekyll = os.path.join(repo_dir, ".nojekyll")
    if not os.path.exists(nojekyll):
        with open(nojekyll, "w") as f:
            f.write("")

    # 5. 清理根目录可能残留的旧版本资源
    _clean_root_legacy_files(repo_dir)

    # 6. git add 仅限本期目录 + 首页 + mascot（避免误提交源码改动）
    paths_to_add = [
        f"episodes/{episode_id}",
        "index.html",
        "mascot.png",
        ".nojekyll",
    ]
    for p in paths_to_add:
        if os.path.exists(p):
            print(f"  📎 git add {p}")
            subprocess.run(["git", "add", p], check=True)
        else:
            print(f"  ⚠️ 路径不存在，跳过 add: {p}")

    commit_msg = f"podcast episode: {episode_id}"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True,
    )
    print(f"  📝 commit: {result.stdout.strip() or result.stderr.strip()}")
    if result.returncode != 0 and "nothing to commit" not in result.stdout + result.stderr:
        if "nothing" not in result.stdout.lower():
            print(f"  ⚠️ commit 异常")

    # 先拉取最新，避免 non-fast-forward 被拒
    print(f"  📥 git pull...")
    subprocess.run(["git", "pull", "--rebase", "origin", "main"],
                   capture_output=True, text=True)

    print(f"  📤 推送到 GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        capture_output=True, text=True,
    )
    print(f"  push stdout: {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"  push stderr: {result.stderr[:300]}")
        raise RuntimeError("git push 失败，请检查 GitHub 凭据")

    url = f"{GITHUB_PAGES_URL}/episodes/{episode_id}/"
    print(f"  ✅ 发布成功！")
    print(f"  📺 本期链接: {url}")
    print(f"  🏠 归档首页: {GITHUB_PAGES_URL}/")
    return url


def _build_episode_meta(episode_id: str, script: dict, chapters: list) -> dict:
    segments = script.get("segments", [])
    duration_sec = chapters[-1]["start_seconds"] if chapters else 0
    cover_image = "image_01.jpg"
    return {
        "episode_id": episode_id,
        "title": script.get("title", "每日AI资讯"),
        "published_at": _format_published(episode_id),
        "duration_seconds": duration_sec,
        "duration_label": _format_duration(duration_sec),
        "cover_image": cover_image,
        "segment_count": len(segments),
        "segments": [
            {
                "title": s.get("news_title", ""),
                "golden_quote": s.get("golden_quote", ""),
                "keywords": s.get("keywords", []),
                "source": s.get("source", ""),
            }
            for s in segments
        ],
    }


def _format_published(episode_id: str) -> str:
    parts = episode_id.split("-")
    if len(parts) >= 4 and len(parts[3]) == 4:
        date = "-".join(parts[:3])
        time = f"{parts[3][:2]}:{parts[3][2:]}"
        return f"{date} {time}"
    return episode_id


def _format_duration(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}分{s:02d}秒"


def _clean_root_legacy_files(repo_dir: str):
    for fname in ("full.mp3", "image_01.jpg", "image_02.jpg",
                  "image_03.jpg", "image_04.jpg", "image_05.jpg"):
        p = os.path.join(repo_dir, fname)
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    from glob import glob
    from config import OUTPUT_DIR

    sites = sorted(glob(os.path.join(OUTPUT_DIR, "site_*")))
    if not sites:
        print("未找到生成好的 site 目录")
    else:
        latest = sites[-1]
        episode_id = os.path.basename(latest).replace("site_", "")
        publish(latest, episode_id)
