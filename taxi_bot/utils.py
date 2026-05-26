
import db
from keyboards import TEXTS





def seed_tariffs():
    db.create_tariff("Start", 5000, 1500)
    db.create_tariff("Comfort", 8000, 1500)
    db.create_tariff("Business", 12000, 1500)

def get_tariff_name(tariff_id):
    tariffs = {
        1: "🚕 Start",
        2: "🚘 Comfort",
        3: "👔 Business"
    }
    return tariffs.get(tariff_id, "Unknown")

