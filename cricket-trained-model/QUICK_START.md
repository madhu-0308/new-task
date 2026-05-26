# Quick Start — Personalized Cricket Coach (5 min)

## 1. Activate environment

```powershell
cd cricket-trained-model
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Run the demo

```powershell
python scripts/demo_personalization.py
```

## 3. Create your profile

```powershell
python src/coach_cli.py user create your_id --name "Your Name" --skill-level intermediate
```

## 4. Predict with tracking

```powershell
python src/predict_personalized.py your_id "cover-drive .mp4" --actual-shot "Cover Drive" --feedback
```

## 5. View reports

```powershell
python src/coach_cli.py report your_id
python src/coach_cli.py session your_id
python src/coach_cli.py stats your_id --days 30
```

## 6. REST API (optional)

```powershell
python scripts/coach_api.py
# Open http://localhost:5000/api/docs
```

Data is stored in `data/user_data.db` (created automatically).
