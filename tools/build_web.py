"""Compile uniquement l'entrée web et le paquet Luna pour un hébergement statique."""
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
STAGE = BUILD / "luna-web"
OUTPUT = ROOT / "dist" / "web"


def clear_generated(path, parent, preserve=()):
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()) or resolved == parent.resolve():
        raise ValueError(f"Dossier généré hors périmètre : {resolved}")
    if path.exists():
        for child in path.iterdir():
            if child.name in preserve:
                continue
            if child.is_symlink() or child.is_file():
                child.unlink()
            else:
                if not child.resolve().is_relative_to(resolved):
                    raise ValueError(f"Dossier généré hors périmètre : {child}")
                shutil.rmtree(child)
    path.mkdir(parents=True, exist_ok=True)


def main():
    clear_generated(STAGE, BUILD)
    shutil.copy2(ROOT / "web/main.py", STAGE / "main.py")
    shutil.copytree(ROOT / "src/luna", STAGE / "luna",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gitkeep"))
    subprocess.run([sys.executable, "-X", "utf8", "-m", "pygbag", "--build", "--no_opt",
                    "--disable-sound-format-error",
                    "--PYBUILD", "3.13", "--width", "1200", "--height", "800",
                    "--title", "Luna — Coupe Fleur",
                    "--template", str(ROOT / "web/template.html"), str(STAGE)],
                   cwd=ROOT, check=True)
    built = STAGE / "build/web"
    if not (built / "index.html").is_file():
        raise RuntimeError("Pygbag n'a pas produit index.html.")
    archive = built / "luna-web.tar.gz"
    with tarfile.open(archive) as package:
        names = package.getnames()
        if not names or any(not (n == "assets/main.py" or n.startswith("assets/luna/")) for n in names):
            raise RuntimeError("Contenu inattendu dans le paquet web.")
    clear_generated(OUTPUT, ROOT / "dist", preserve=(".vercel",))
    for name in ("index.html", "favicon.png", "luna-web.tar.gz", "luna-web.apk"):
        shutil.copy2(built / name, OUTPUT / name)
    shutil.copy2(ROOT / "web/vercel.json", OUTPUT / "vercel.json")
    print(f"Sortie : {OUTPUT}")
    print("Serveur : .venv/Scripts/python.exe -m http.server 8000 --directory dist/web")


if __name__ == "__main__":
    main()
