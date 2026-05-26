# Cricket Shot Classifier — Team Training Guide

Onboarding for anyone helping train / improve the cricket shot classifier.
Read this once, then follow the steps. Estimated first run: 3-4 hours.

---

## What we're building

A classifier that takes a short cricket clip and predicts which shot it was:
**drive · cut · pull_hook · sweep · defensive · glance · innovative**

The model is a small PyTorch Transformer over pose keypoints extracted by YOLO-Pose.

- **Backend** (already deployed): `https://macharlamadhu47-classifier.hf.space`
- **Frontend** (already deployed): `https://cric2-fawn.vercel.app`
- **Training pipeline** (you'll run): everything in this folder

Your job: **make the model better** by adding cleaner training data and retraining.

---

## Prerequisites

Install once on your machine (Windows shown — adapt for macOS/Linux):

1. **Python 3.10+** — https://python.org/downloads
2. **ffmpeg** — `winget install ffmpeg` OR https://www.gyan.dev/ffmpeg/builds/ (add to PATH)
3. **Git** — https://git-scm.com/downloads
4. **A decent disk** — full dataset can hit 5 GB; plan for it

Verify:
```cmd
python --version       # >= 3.10
ffmpeg -version
git --version
```

---

## One-time setup

```cmd
cd F:\cricket-shot-analysis           :: or wherever you cloned this
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

The `pip install` downloads ~2 GB (PyTorch + Ultralytics). Takes 5-10 min, once.

You'll know venv is active when your prompt shows `(.venv)`.

---

## The training pipeline (6 scripts, run in order)

Every time you want to retrain with new data:

```cmd
.\.venv\Scripts\activate.bat

python scripts\download_videos.py    :: 1. download YouTube videos to data\raw_videos\<class>\
python scripts\segment_clips.py      :: 2. cut each video into per-shot clips
python scripts\review_clips.py       :: 3. MANUAL — keep good clips, trash bad ones
python scripts\extract_poses.py      :: 4. run YOLO-Pose, save keypoint sequences
python scripts\make_splits.py        :: 5. train/val/test split
python src\train.py                  :: 6. train the Transformer
```

Output: `F:\cricket-shot-analysis\runs\exp1\best.pt` — the new trained model.

---

## How to add new training data (the most useful task)

This is what you'll mostly be doing.

### 1. Find good YouTube videos

Search for cricket compilations of a **single shot type**:
- "Virat Kohli cover drive compilation"
- "best square cut shots cricket"
- "Ricky Ponting pull shot best"
- "Pietersen switch hit"

**Prefer LONG-FORM videos** (5-15 min) from coaching channels.
**Avoid YouTube Shorts** — they're usually mixed highlight reels that pollute the data.

Avoid:
- Slow-mo replay-only compilations
- Highlight reels with mixed shots
- Pure batting summaries (too many cuts)

### 2. Paste URLs into the config file

Open `scripts\urls_by_class.yaml` in any text editor. Add URLs under the matching class:

```yaml
cut:
  urls:
    - https://youtu.be/abcdefghij
    - https://youtu.be/klmnopqrst
```

Indentation matters: exactly two spaces, then `- ` before each URL.

### 3. Run the pipeline

```cmd
python scripts\download_videos.py
```

Downloads all NEW URLs (skips ones already downloaded). ~10-30 min.

```cmd
python scripts\segment_clips.py
```

Cuts each video into per-shot candidate clips. ~10-30 min.

```cmd
python scripts\review_clips.py
```

**The hardest part.** A window opens looping each clip. For each clip, press:
- `k` or `SPACE` — keep (the clip clearly shows the labeled shot)
- `x` — trash (anything that ISN'T clearly the labeled shot)
- `z` — undo last move
- `Q` (capital) — quit, resume later with `--start N`

**Be ruthless. Trash 50-60% of clips.** If you can't tell what shot it is in 2 sec, press `x`. If you're not sure, press `x`. Quality > quantity.

```cmd
python scripts\extract_poses.py
python scripts\make_splits.py
python src\train.py
```

These run themselves. Total ~30-90 min.

At the end of `train.py`, you'll see a confusion matrix and per-class recall. **Note the test accuracy** — that's our score.

---

## After training: upload the new model

```powershell
copy "F:\cricket-shot-analysis\runs\exp1\best.pt" "F:\hf-space-cricket\shot_classifier\weights\best.pt"
$env:HF_TOKEN = "hf_YOUR_TOKEN"
& "F:\cricket-shot-analysis\.venv\Scripts\python.exe" "F:\hf-space-cricket\_upload.py"
$env:HF_TOKEN = $null
```

Get your `hf_...` Write token at https://huggingface.co/settings/tokens (must be **Write**, not Read).
Ask the project owner to add you as a contributor on the HF Space first.

HF Space rebuilds in 2-3 min. New predictions live on the public website.

---

## Current state (so you know where we are)

| Class | Train samples | Test recall (latest) |
|---|---|---|
| defensive | 75+ | 85% ✓ |
| innovative | 22+ | 37-65% (varies) |
| drive | 39+ | 27-78% (varies) |
| pull_hook | 12-30+ | 34-67% |
| sweep | 19+ | 6-24% ✗ |
| cut | 9-20+ | 20-50% |
| glance | 0-1 | not trained |

**Test accuracy bounces between 40% and 58%** because:
1. We have <1000 training samples total — too few
2. Many existing clips are mislabeled (from mixed-content Shorts)

**Biggest improvement available:** re-run `review_clips.py` on ALL existing clips with the "be ruthless" rule. Expected jump: 40% → 65-75%.

After data is clean, more URLs help. Before that, more URLs probably hurt.

---

## What to coordinate with the team

1. **Don't all add URLs at the same time** — merge conflicts on `urls_by_class.yaml`
2. **One person at a time runs the pipeline** — model file is shared
3. **Always paste your final test accuracy** to the team channel after training
4. **Don't commit `data/` or `runs/`** to git — too big, already in `.gitignore`
5. **Only the project owner has the HF Write token** — they upload the final model

---

## 🚀 PARALLEL WORKFLOW — split work across the team for 4× speed

If you have 3-5 people, divide shots between them and work simultaneously. Roughly 4× faster wall-clock time.

### Assign one shot per person

Example for a 4-person team:

| Person | Class(es) assigned |
|---|---|
| Person A | `cut` + `sweep` |
| Person B | `drive` + `pull_hook` |
| Person C | `defensive` + `glance` |
| Person D | `innovative` |
| You (owner) | coordinator + final training + HF upload |

### What each teammate runs (their class only)

Every script supports a `--class` flag. They only work on their assigned class — no conflicts with anyone else's files.

```cmd
:: Person A example, working on 'cut'
.\.venv\Scripts\activate.bat

python scripts\download_videos.py --class cut
python scripts\segment_clips.py --class cut
python scripts\review_clips.py --class cut
```

### What teammates send back to the owner

After review, zip the per-class clip folder and send to the owner:

```powershell
:: From the teammate's machine, after review
Compress-Archive -Path "data\clips\cut" -DestinationPath "cut_clips.zip"
```

Send the ZIP via Google Drive / WhatsApp / Telegram / email. Usually 30-100 MB per class.

### What the owner does after collecting everyone's ZIPs

1. Extract each ZIP into the matching folder:
   ```powershell
   Expand-Archive -Path "cut_clips.zip" -DestinationPath "data\clips\" -Force
   ```
   (Drops the `cut` folder back into `data\clips\cut`, overwriting old data.)

2. Repeat for each teammate's ZIP.

3. Run the final 3 steps ONCE on the combined data:
   ```cmd
   python scripts\extract_poses.py
   python scripts\make_splits.py
   python src\train.py
   ```

4. Upload the new `best.pt` to HF Space (only the owner does this).

### Notes for teammates

- **Don't train locally** — that wastes time. Only the owner runs `train.py` after combining everyone's data.
- **Be ruthless during review.** Trash anything that isn't clearly your assigned shot.
- **Quality > quantity.** 50 clean clips beats 200 noisy ones.
- **Send your ZIP + a one-line summary**: "Cut class: kept 45 clips of 132, trashed mixed-content highlights and crowd shots."

### Estimated parallel timeline

| Phase | Sequential (1 person) | Parallel (4 people) |
|---|---|---|
| Download + segment + review all classes | 10-15 hours | 2-3 hours wall-clock |
| Extract + train + upload (owner) | 1 hour | 1 hour |
| **Total** | **11-16 hours** | **3-4 hours** |

---

## When to stop adding data and start improving the model

When **test accuracy plateaus** (3 retrains in a row with new data don't improve it).

At that point, talk to the owner about:
- Migrating backend to Modal Labs (faster CPU)
- Adding bat tracking via Roboflow
- Trying a bigger pose model (yolov8s-pose)
- Trying ONNX for faster inference

These are roadmap items; don't do them solo.

---

## Common errors and fixes

| Error | Fix |
|---|---|
| `No module named 'torch'` | Venv not activated. Run `.\.venv\Scripts\activate.bat`. Prompt should show `(.venv)`. |
| `ffmpeg failed` | ffmpeg not on PATH. Reinstall and confirm `ffmpeg -version` works. |
| `No URLs provided` | You forgot to add URLs to `urls_by_class.yaml`. |
| Camera permission errors | Not relevant for training — only for the live site. |
| HF token "Read-only" error | Created a Read token instead of Write. Make a new Write token. |
| Out of disk space | Delete old videos: `data\raw_videos\<class>\*.mp4` (segments and poses stay). |

---

## Questions?

Ping the project owner. Don't push to GitHub or upload to HF without coordinating — it overwrites the production model.
