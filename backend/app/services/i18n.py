
# Simple translation dictionary
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "order_confirmed": "Your order has been confirmed.",
        "low_stock": "Insufficient stock for product.",
        "not_authorized": "Insufficient permissions."
    },
    "my": {
        "order_confirmed": "သင့်အော်ဒါ အတည်ပြုပြီးပါပြီ။",
        "low_stock": "ပစ္စည်းလက်ကျန် မလုံလောက်ပါ။",
        "not_authorized": "ခွင့်ပြုချက် မရှိပါ။"
    },
    "th": {
        "order_confirmed": "คำสั่งซื้อของคุณได้รับการยืนยันแล้ว",
        "low_stock": "สินค้าคงคลังไม่เพียงพอ",
        "not_authorized": "ไม่มีสิทธิ์ในการดำเนินการ"
    }
}

def translate(key: str, lang: str = "en") -> str:
    """Returns localized string for a given key and language code."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return lang_dict.get(key, key)
