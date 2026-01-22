import os

def save_text_files(base_dir, base_name, handwritten, printed, save_detailed=False):
    os.makedirs(base_dir, exist_ok=True)
    h_path = os.path.join(base_dir, f"{base_name}_chu_viet_tay.txt")
    p_path = os.path.join(base_dir, f"{base_name}_chu_in.txt")
    try:
        with open(h_path, "w", encoding="utf-8") as f:
            for item in handwritten:
                f.write(item.get("text","") + "\n")
                if save_detailed:
                    f.write(f"confidence: {item.get('confidence')}\n")
        with open(p_path, "w", encoding="utf-8") as f:
            for item in printed:
                f.write(item.get("text","") + "\n")
                if save_detailed:
                    f.write(f"confidence: {item.get('confidence')}\n")
    except Exception as e:
        print(f"⚠️ Lỗi lưu file: {e}")
    return h_path, p_path