# Backup Completeness Audit Report

**Date**: 2026-04-13T09:44
**Task**: cmd_1367 / subtask_1367a
**Auditor**: ashigaru3

## Executive Summary

Total project size: **~931GB** (projects/ 468GB + tools/ 6.4GB + venv_whisper/ 4.9GB + queue/ 1.7GB + logs/ 105MB + work/ 407MB + config/ 44KB + orders/ 168KB)

**GitHub-tracked**: ~1.5GB (scripts, instructions, skills, templates, submodule pointers)
**Not backed up**: ~929GB — most is media/regenerable, but **config/secrets** and **queue/operational state** are critical gaps.

## Risk Classification

| Risk Level | Meaning |
|------------|---------|
| **HIGH** | Loss = service disruption, cannot recover without human intervention |
| **MEDIUM** | Loss = significant rework (hours-days), but data is regenerable |
| **LOW** | Loss = minor inconvenience, fully rebuildable from public sources |

---

## 1. projects/ — 468GB

### 1.1 dozle_kirinuki — 449GB [MEDIUM]

- **Git repo**: naginata63/dozle_kirinuki (submodule)
- **Tracked files**: 12,808 files (scripts, config, context, panel JSONs)
- **Untracked**: `work/` = 433GB (video files, manga outputs, SRT, clips, etc.)
- **Backup status**: Scripts/config backed up to GitHub. Media files are NOT backed up.
- **Rebuildability**: Scripts fully recoverable. Media files (downloaded YouTube videos, generated manga panels) would require re-downloading ~400GB and re-running expensive API calls.
- **Risk**: MEDIUM — media is regenerable but would cost significant time (days) and API fees (Gemini API for manga generation).

### 1.2 coconala-tools — 26MB [LOW]

- **Git repo**: naginata63/coconala-tools (submodule)
- **Tracked files**: 203 files
- **Backup status**: Fully backed up to GitHub.
- **Risk**: LOW

### 1.3 note_mcp_server — 131MB [LOW]

- **Git repo**: naginata63/note-scripts (submodule)
- **Backup status**: Fully backed up to GitHub.
- **Risk**: LOW

### 1.4 crowdworks_china_shorts — 4.4GB [HIGH]

- **Git repo**: NONE
- **Backup status**: NOT BACKED UP
- **Contents**: Video editing project for CrowdWorks China shorts
- **Rebuildability**: Videos would need re-downloading. Edit decisions/scripts may be lost.
- **Risk**: HIGH — unique project data with no backup.

### 1.5 crowdworks_video_edit — 15GB [HIGH]

- **Git repo**: NONE
- **Backup status**: NOT BACKED UP
- **Contents**: Video editing project (cut_edited.mp4, telop.ass, broll images, reference video)
- **Rebuildability**: Some files regenerable, but edit decisions and composed outputs are unique.
- **Risk**: HIGH — active project with unique composed video artifacts.

### 1.6 narration_sample — 225MB [MEDIUM]

- **Git repo**: NONE
- **Backup status**: NOT BACKED UP
- **Contents**: Voice narration samples
- **Rebuildability**: Samples may be re-recordable but voice quality may differ.
- **Risk**: MEDIUM

### 1.7 ec_description_tool — 6.8MB [MEDIUM]

- **Git repo**: NONE (remote points to coconala-tools but no local .git)
- **Backup status**: UNCERTAIN
- **Risk**: MEDIUM

### 1.8 email_reply_tool — 11MB [MEDIUM]

- **Git repo**: NONE (same as above)
- **Risk**: MEDIUM

### 1.9 review_reply_tool — 3.8MB [MEDIUM]

- **Git repo**: NONE
- **Risk**: MEDIUM

### 1.10 sns_post_tool — 4.8MB [MEDIUM]

- **Git repo**: NONE
- **Risk**: MEDIUM

### 1.11 trial_video_editing — 36KB [LOW]

- **Git repo**: NONE
- **Contents**: Minimal trial files
- **Risk**: LOW

### 1.12 projects/projects — 300KB [LOW]

- **Git repo**: NONE
- **Risk**: LOW

---

## 2. config/ — 44KB [HIGH — SECRETS]

- **Git tracking**: Only `settings.yaml`, `ntfy_auth.env.sample`, `voicevox_dict.txt`, `genai_user_profile.yaml` are whitelisted
- **Untracked secrets**:
  - `glm_api_key.env` — Z.AI/GLM API key
  - `vertex_api_key.env` — Vertex ADC auth config
  - `discord_bot.env` — Discord bot token + channel ID
  - `replicate.env` — Replicate API token + BFL API key
  - `config.json` — Additional config
  - `projects.yaml` — Project routing config
- **Backup status**: NOT BACKED UP. If lost, all API keys must be regenerated from respective provider consoles.
- **Risk**: HIGH — secrets are irreplaceable without manual provider console access.
- **Recommendation**: Use a secrets manager (e.g., `pass`, `gpg`-encrypted backup, or cloud secret manager). Never commit to git.

---

## 3. queue/ — 1.7GB [HIGH — OPERATIONAL STATE]

- **Git tracking**: NOT tracked (queue/precompact/ explicitly ignored)
- **Contents**:
  - `tasks/*.yaml` — Current task assignments for all agents
  - `inbox/*.yaml` — Agent inbox messages
  - `reports/*.yaml` — Historical task completion reports
  - `shogun_to_karo.yaml` — Command queue (active commands)
  - `metrics/` — Advisor proxy metrics
  - `archive/`, `cmd_archive/` — Historical archives
- **Backup status**: NOT BACKED UP
- **Risk**: HIGH — complete operational state. Loss = all agents lose context, active tasks lost, no recovery possible without manual reconstruction.
- **Recommendation**: Periodic sync to private GCS bucket or separate private git repo.

---

## 4. work/ — 407MB [MEDIUM]

- **Git tracking**: Mostly NOT tracked (only `work/cmd_1039/articles/` whitelisted)
- **Contents**:
  - `sasuu_articles/` — 292MB of article data
  - `dingtalk_qc/` — DingTalk QC data and README
  - `dingtalk_manual_*.pdf` — DingTalk operation manuals (33MB)
  - Various cmd intermediate outputs
- **Backup status**: NOT BACKED UP
- **Risk**: MEDIUM — mostly regenerable, but DingTalk manuals and QC data are unique.

---

## 5. tools/ — 6.4GB [LOW]

- **Git tracking**: NOT tracked
- **Contents**:
  - `COEIROINK_LINUX_GPU_v.2.13.0/` — TTS engine (downloadable)
  - `video-subtitle-remover/` — Video tool (downloadable from GitHub)
- **Backup status**: NOT BACKED UP
- **Risk**: LOW — third-party tools, fully rebuildable from original sources.

---

## 6. orders/ — 168KB [LOW]

- **Git tracking**: Submodule — naginata63/multi-agent-orders.git
- **Backup status**: Fully backed up to GitHub.
- **Risk**: LOW

---

## 7. logs/ — 105MB [LOW]

- **Git tracking**: NOT tracked
- **Contents**: advisor_proxy.log, cmd_rag.log, genai_daily.log, ntfy logs, backup snapshots
- **Backup status**: NOT BACKED UP
- **Risk**: LOW — ephemeral operational logs. Useful for debugging but not critical.

---

## 8. venv_whisper/ — 4.9GB [LOW]

- **Git tracking**: NOT tracked
- **Contents**: Python virtual environment for WhisperX STT
- **Backup status**: NOT BACKED UP
- **Risk**: LOW — fully rebuildable from `requirements.txt` + pip install.

---

## 9. .claude/ memory [MEDIUM]

### Claude Code memory (~55 files)
- **Location**: `~/.claude/projects/-home-murakami-multi-agent-shogun/memory/`
- **Contents**: MEMORY.md (index) + 55 feedback/project/reference memory files
- **Backup status**: NOT BACKED UP — Claude Code internal storage
- **Risk**: MEDIUM — accumulated organizational knowledge. Loss = agents lose learned preferences and lessons.

### GLM memory (2 files)
- **Location**: `~/.claude_glm/.claude/projects/-home-murakami-multi-agent-shogun/memory/`
- **Contents**: MEMORY.md + feedback_inbox_spam_ban.md
- **Risk**: LOW — minimal content

---

## 10. shared_context/ — MEDIUM

- **Git tracking**: Only `README.md` tracked. 19 other files NOT tracked.
- **Contents**: Procedures, design docs, QC templates, collective intelligence results
- **Backup status**: NOT BACKED UP
- **Risk**: MEDIUM — valuable procedural knowledge. Some files are regenerable, others (collective results) required expensive multi-agent computation.

---

## 11. dashboard.md — 25KB [LOW]

- **Git tracking**: TRACKED in main repo
- **Backup status**: Backed up to GitHub
- **Risk**: LOW

---

## Priority Action Items

### Immediate (HIGH risk, quick wins)

| # | Item | Action | Effort |
|---|------|--------|--------|
| 1 | config/ secrets | Encrypt and store in private GCS bucket or separate private repo | 1h |
| 2 | queue/ operational state | Set up cron sync to private GCS bucket (`gsutil -m rsync`) | 2h |
| 3 | crowdworks_china_shorts/ | Create private GitHub repo and push | 30min |
| 4 | crowdworks_video_edit/ | Create private GitHub repo and push (git-lfs for large files) | 1h |

### Short-term (MEDIUM risk)

| # | Item | Action | Effort |
|---|------|--------|--------|
| 5 | shared_context/ procedures | Add to git tracking or sync to private repo | 30min |
| 6 | work/dingtalk_* | Back up DingTalk manuals and QC data | 15min |
| 7 | crowdworks sub-tools (ec, email, review, sns) | Consolidate into coconala-tools submodule or separate repos | 2h |
| 8 | .claude/ memory | Periodic export to git-tracked location | 1h |

### Long-term (LOW risk, optional)

| # | Item | Action | Effort |
|---|------|--------|--------|
| 9 | projects/dozle_kirinuki/work/ | Evaluate GCS cold storage for media archive | 4h |
| 10 | tools/ | Document download URLs and versions for rebuild | 1h |
| 11 | logs/ | Implement log rotation with S3/GCS archival | 2h |

---

## Summary Statistics

| Category | Total Size | Git-Tracked | Not Backed Up | Risk |
|----------|-----------|-------------|---------------|------|
| projects/ (submoduled) | 580GB | ~500MB | ~579GB | LOW-MED |
| projects/ (no repo) | 20GB | 0 | 20GB | HIGH |
| config/ | 44KB | ~10KB | ~34KB (secrets) | HIGH |
| queue/ | 1.7GB | 0 | 1.7GB | HIGH |
| work/ | 407MB | ~5MB | ~400MB | MEDIUM |
| shared_context/ | ~2MB | ~1KB | ~2MB | MEDIUM |
| .claude/ memory | ~60KB | 0 | ~60KB | MEDIUM |
| tools/ | 6.4GB | 0 | 6.4GB | LOW |
| logs/ | 105MB | 0 | 105MB | LOW |
| venv_whisper/ | 4.9GB | 0 | 4.9GB | LOW |
| orders/ | 168KB | 168KB | 0 | LOW |
| dashboard.md | 25KB | 25KB | 0 | LOW |

**Grand total not backed up**: ~612GB (of which ~600GB is media/regenerable, ~12GB is unique data at risk)
