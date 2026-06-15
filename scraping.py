import time
import re
import warnings
from datetime import datetime, timezone
import requests
import pandas as pd


def clean_names(name:str)->str:
    name = re.sub(r"[^a-zA-Z0-9]", "_", str(name))
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name


def get_efi_partido(match_id: int) -> pd.DataFrame | None:
    time.sleep(2)

    url=f"https://fdh-api.fifa.com/v1/stats/match/{match_id}/players.json"

    try:
        resp=requests.get(url,timeout=30)
        resp.raise_for_status()
        data=resp.json()

        rows=[]

        for player_id,metrics in data.items():
            row={
                "player_id":int(player_id),
                "match_id":match_id
            }
            for metric in metrics:
                metric_name,metric_value=metric[0],metric[1]
                row[metric_name]=metric_value
            
        if not rows:
            return None

        stats = pd.DataFrame(rows)
        stats.columns = [clean_names(c) for c in stats.columns]

        print(f" Partido {match_id} descargado ({len(stats)} jugadores)")
        return stats

    except Exception as e:
        warnings.warn(f"✗ Partido {match_id} falló: {e}")
        return None

matches = pd.read_csv("data/wc2026_matches.csv")
players = pd.read_csv("data/wc2026_players.csv")

now = datetime.now(timezone.utc)
matches["date"] = pd.to_datetime(matches["date"], utc=True)
played = matches[matches["date"] < now]
ids = played["result_id"].tolist()

frames = [get_efi_partido(match_id) for match_id in ids]
all_stats_efi = pd.concat([f for f in frames if f is not None], ignore_index=True)

data_efi = all_stats_efi.merge(players, on="player_id", how="inner")

data_efi.to_csv("data/wc2026_efi.csv", index=False)
print(f"\n Guardado data/wc2026_efi.csv ({len(data_efi)} filas)")
