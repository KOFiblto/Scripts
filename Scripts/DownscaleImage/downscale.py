import sys
import os
import traceback
import ctypes

def basic_error(msg):
    print("\n" + "!"*60)
    print("KRITISCHER FEHLER BEIM START (Import-Fehler?):")
    print(msg)
    print("!"*60)
    ctypes.windll.user32.MessageBoxW(0, msg, "Downscale Start Error", 0x10)
    input("\nDruecke Enter zum Beenden...")
    sys.exit(1)

try:
    import math
    import shutil
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    basic_error(traceback.format_exc())

def show_error(err_msg):
    # Try to show error in console
    print("\n" + "="*50)
    print("FEHLER AUFGETRETEN:")
    print(err_msg)
    print("="*50)
    # Also show a message box in case it's run without console
    ctypes.windll.user32.MessageBoxW(0, err_msg, "Downscale Error", 0x10)
    input("\nDruecke Enter zum Beenden...")
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: downscale.py <image_path> <target_mp>")
        sys.exit(1)

    image_path = sys.argv[1]
    target_mp_arg = int(sys.argv[2])
    target_mp = target_mp_arg * 1000000

    print(f"Skript gestartet. Bild: {image_path}, Ziel: {target_mp_arg}MP")

    img = Image.open(image_path)
    current_mp = img.width * img.height
    print(f"Originalbild: {img.width}x{img.height} Pixel ({current_mp} Gesamtpixel)")

    scale = 1.0
    if current_mp > target_mp:
        scale = math.sqrt(target_mp / current_mp)

    new_w = max(64, round((img.width * scale) / 64) * 64)
    new_h = max(64, round((img.height * scale) / 64) * 64)
    print(f"Berechnete Zielaufloesung (div64): {new_w}x{new_h} Pixel")

    ext = os.path.splitext(image_path)[1].lower()
    is_webp = (ext == '.webp')

    dir_name = os.path.dirname(image_path)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    sub_dir = os.path.join(dir_name, f"{target_mp_arg}MP")
    os.makedirs(sub_dir, exist_ok=True)

    out_ext = '.jpg' if is_webp else ext
    new_path = os.path.join(sub_dir, f"{base_name}__{target_mp_arg}MP{out_ext}")

    # FIX: If already correct size and not webp, copy instead of abort
    if new_w == img.width and new_h == img.height and not is_webp:
        print(f"Bild entspricht bereits den Vorgaben. Kopiere nach: {new_path}")
        shutil.copy2(image_path, new_path)
        return

    img_resized = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

    if is_webp and img_resized.mode in ("RGBA", "P"):
        img_resized = img_resized.convert("RGB")

    save_kwargs = {}
    if out_ext in ['.jpg', '.jpeg']:
        if img.format == 'JPEG':
            save_kwargs['quality'] = 'keep'
        else:
            save_kwargs['quality'] = 100
    elif out_ext == '.avif':
        save_kwargs['format'] = 'AVIF'

    try:
        img_resized.save(new_path, **save_kwargs)
        print(f"Erfolg: Gespeichert unter {new_path}")
    except ValueError:
        save_kwargs['quality'] = 100
        img_resized.save(new_path, **save_kwargs)
        print(f"Erfolg (Fallback Quality 100): Gespeichert unter {new_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        show_error(traceback.format_exc())