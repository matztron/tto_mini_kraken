#!/usr/bin/env python3
"""Rasterize mini_kraken.png into IHP TopMetal1 GDS + LEF for Tiny Tapeout."""

from __future__ import annotations

from pathlib import Path

import gdstk
from PIL import Image

# --- paths ---
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PNG_PATH = HERE / "mini_kraken.png"
OUT_DIR = REPO / "macros"

CELL_NAME = "mini_kraken"
PIXEL_UM = 3.0  # ~72 µm for 24x24; keep >= ~2.0 for TopMetal1 DRC

# IHP SG13G2 (Tiny Tapeout silicon-art guide)
ART_LAYER = 126          # TopMetal1
ART_DATATYPE = 0
BOUNDARY_LAYER = 189     # prBoundary
BOUNDARY_DATATYPE = 4


def write_lef(path: Path, cell_name: str, width: float, height: float) -> None:
    path.write_text(
        f"""# LEF generated for {cell_name}
VERSION 5.8 ;
NAMESCASESENSITIVE ON ;
DIVIDERCHAR "/" ;
BUSBITCHARS "[]" ;
UNITS
   DATABASE MICRONS 1000 ;
END UNITS

MACRO {cell_name}
   CLASS BLOCK ;
   FOREIGN {cell_name} 0 0 ;
   SIZE {width:.3f} BY {height:.3f} ;
   SYMMETRY X Y ;
END {cell_name}
"""
    )


def main() -> None:
    if not PNG_PATH.is_file():
        raise SystemExit(f"missing PNG: {PNG_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    im = Image.open(PNG_PATH).convert("RGBA")
    w, h = im.size
    pixels = im.load()

    lib = gdstk.Library()
    cell = lib.new_cell(CELL_NAME)

    width_um = w * PIXEL_UM
    height_um = h * PIXEL_UM

    # Place-and-route footprint (required)
    cell.add(
        gdstk.rectangle(
            (0, 0),
            (width_um, height_um),
            layer=BOUNDARY_LAYER,
            datatype=BOUNDARY_DATATYPE,
        )
    )

    metal = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            # Your art is opaque black on transparent → metal = opaque
            if a < 128:
                continue
            # PNG y=0 is top; GDS y grows upward
            x0 = x * PIXEL_UM
            y0 = (h - 1 - y) * PIXEL_UM
            cell.add(
                gdstk.rectangle(
                    (x0, y0),
                    (x0 + PIXEL_UM, y0 + PIXEL_UM),
                    layer=ART_LAYER,
                    datatype=ART_DATATYPE,
                )
            )
            metal += 1

    gds_path = OUT_DIR / f"{CELL_NAME}.gds"
    lef_path = OUT_DIR / f"{CELL_NAME}.lef"
    svg_path = OUT_DIR / f"{CELL_NAME}.svg"

    lib.write_gds(str(gds_path))
    write_lef(lef_path, CELL_NAME, width_um, height_um)
    cell.write_svg(str(svg_path))

    print(f"PNG:    {PNG_PATH} ({w}x{h})")
    print(f"metal:  {metal} pixels @ {PIXEL_UM} µm → {width_um:.1f} x {height_um:.1f} µm")
    print(f"wrote:  {gds_path}")
    print(f"        {lef_path}")
    print(f"        {svg_path}")


if __name__ == "__main__":
    main()