"""
Otimiza as imagens do site Sweet Cake.

- Reduz imagens muito largas para LARGURA_MAX pixels (mantém a proporção).
- Recomprime no MESMO formato e com o MESMO nome de arquivo, então nenhum
  caminho no HTML, no CSS ou no banco de dados (imagem_url) precisa mudar.
- Só grava o arquivo novo se ele ficar pelo menos 5% menor que o original.

Uso (na raiz do projeto, no PowerShell):

    pip install pillow
    python otimizar_imagens.py                 # simulação: só mostra o que faria
    python otimizar_imagens.py --aplicar       # grava de verdade

Antes de usar --aplicar, faça um commit (ou copie a pasta) para poder desfazer:
    git restore frontend/assets/images
"""
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

# Pasta de imagens: pode ser passada como argumento (sem as flags "--").
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PASTA = Path(args[0]) if args else Path("frontend/assets/images")
APLICAR = "--aplicar" in sys.argv

LARGURA_MAX = 1000   # px. Os cards aparecem com ~370 px; 1000 cobre telas retina
QUALIDADE_WEBP = 78
QUALIDADE_JPEG = 80
GANHO_MINIMO = 0.05  # só grava se economizar pelo menos 5%


def otimizar(caminho: Path):
    """Devolve (bytes_originais, bytes_novos, largura_antes, largura_depois)."""
    ext = caminho.suffix.lower()
    original = caminho.stat().st_size

    with Image.open(caminho) as img:
        if getattr(img, "is_animated", False):
            return original, None, img.width, img.width  # não mexe em animações

        img = ImageOps.exif_transpose(img)  # respeita a rotação gravada pela câmera
        largura_antes = img.width

        if img.width > LARGURA_MAX:
            altura = round(img.height * LARGURA_MAX / img.width)
            img = img.resize((LARGURA_MAX, altura), Image.LANCZOS)

        buf = BytesIO()
        if ext == ".webp":
            img.save(buf, "WEBP", quality=QUALIDADE_WEBP, method=6)
        elif ext in (".jpg", ".jpeg", ".jfif"):
            img.convert("RGB").save(
                buf, "JPEG", quality=QUALIDADE_JPEG, optimize=True, progressive=True
            )
        elif ext == ".png":
            img.save(buf, "PNG", optimize=True)
        else:
            return original, None, largura_antes, largura_antes

        return original, buf.getvalue(), largura_antes, img.width


def main():
    if not PASTA.exists():
        sys.exit(f"Pasta não encontrada: {PASTA.resolve()}")

    formatos = {".webp", ".jpg", ".jpeg", ".jfif", ".png"}
    arquivos = sorted(p for p in PASTA.rglob("*") if p.suffix.lower() in formatos)

    total_antes = total_depois = 0
    print(f"{'ANTES':>9} {'DEPOIS':>9}  {'LARGURA':>13}  ARQUIVO")

    for p in arquivos:
        try:
            antes, novo, larg_antes, larg_depois = otimizar(p)
        except Exception as erro:  # arquivo corrompido, formato estranho etc.
            print(f"{'-':>9} {'-':>9}  {'-':>13}  {p.relative_to(PASTA)}  (erro: {erro})")
            continue

        total_antes += antes
        if novo is None or len(novo) > antes * (1 - GANHO_MINIMO):
            total_depois += antes
            continue  # não compensa: mantém o original

        total_depois += len(novo)
        if APLICAR:
            p.write_bytes(novo)
        print(
            f"{antes / 1024:7.0f}KB {len(novo) / 1024:7.0f}KB  "
            f"{larg_antes:>5} -> {larg_depois:<5}  {p.relative_to(PASTA)}"
        )

    economia = total_antes - total_depois
    print("-" * 60)
    print(
        f"Total: {total_antes / 1024 / 1024:.1f} MB -> {total_depois / 1024 / 1024:.1f} MB "
        f"(economia de {economia / 1024 / 1024:.1f} MB)"
    )
    if not APLICAR:
        print("\nSIMULAÇÃO: nada foi gravado. Rode com --aplicar para salvar.")


if __name__ == "__main__":
    main()
