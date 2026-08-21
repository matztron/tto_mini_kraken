#!/usr/bin/env python3
"""Rasterize heart_a.png into IHP TopMetal1 GDS + LEF for Tiny Tapeout.

Fixes Magic TM1.a / TM1.b (Metal6 min width/spacing ~1.64 µm) by:
  - using a larger pixel pitch than the minimum rule
  - boolean-OR merging abutting pixel rectangles into solid polygons
    (avoids thin necks at diagonal staircase jogs)
"""

from __future__ import annotations

from pathlib import Path

import gdstk
from PIL import Image

# --- paths ---
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PNG_PATH = HERE / "heart_a.png"
OUT_DIR = REPO / "macros"

CELL_NAME = "mini_kraken"

# Fit inside one PDN bay (pitch 38.87 µm): total macro < ~30 µm.
# TopMetal1 min width/spacing ≈ 1.64 µm → pixel pitch must stay above that.
GRID_PX = 16  # downsample 24x24 artwork for the small sticker
PIXEL_UM = 1.7
PIXEL_DRAW_UM = 1.75  # slight overlap before boolean merge
MARGIN_UM = 1.0

# IHP SG13G2 (Tiny Tapeout silicon-art guide)
ART_LAYER = 126  # TopMetal1
ART_DATATYPE = 0
BOUNDARY_LAYER = 189  # prBoundary
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


def opaque_mask(im: Image.Image) -> list[list[bool]]:
    """True where PNG is opaque (metal)."""
    w, h = im.size
    pixels = im.load()
    return [[pixels[x, y][3] >= 128 for x in range(w)] for y in range(h)]


def thicken_diagonals(mask: list[list[bool]]) -> list[list[bool]]:
    """Fill empty pixels that sit between diagonal-only metal (closes TM1 jogs)."""
    h = len(mask)
    w = len(mask[0])
    out = [row[:] for row in mask]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                continue
            # NW-SE diagonal pair
            nw = y > 0 and x > 0 and mask[y - 1][x - 1]
            se = y + 1 < h and x + 1 < w and mask[y + 1][x + 1]
            # NE-SW diagonal pair
            ne = y > 0 and x + 1 < w and mask[y - 1][x + 1]
            sw = y + 1 < h and x > 0 and mask[y + 1][x - 1]
            if (nw and se) or (ne and sw):
                out[y][x] = True
    return out


def main() -> None:
    if not PNG_PATH.is_file():
        raise SystemExit(f"missing PNG: {PNG_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    im = Image.open(PNG_PATH).convert("RGBA")
    if im.size != (GRID_PX, GRID_PX):
        im = im.resize((GRID_PX, GRID_PX), getattr(Image, "Resampling", Image).NEAREST)
    w, h = im.size
    mask = thicken_diagonals(opaque_mask(im))

    lib = gdstk.Library()
    cell = lib.new_cell(CELL_NAME)

    art_w = w * PIXEL_UM
    art_h = h * PIXEL_UM
    width_um = art_w + 2 * MARGIN_UM
    height_um = art_h + 2 * MARGIN_UM
    if width_um >= 30.0 or height_um >= 30.0:
        raise SystemExit(
            f"macro {width_um:.1f}x{height_um:.1f} µm exceeds <30 µm PDN-bay budget"
        )

    # Place-and-route footprint (required)
    cell.add(
        gdstk.rectangle(
            (0, 0),
            (width_um, height_um),
            layer=BOUNDARY_LAYER,
            datatype=BOUNDARY_DATATYPE,
        )
    )

    rects: list[gdstk.Polygon] = []
    metal = 0
    inset = (PIXEL_DRAW_UM - PIXEL_UM) / 2.0
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            # PNG y=0 is top; GDS y grows upward
            x0 = MARGIN_UM + x * PIXEL_UM - inset
            y0 = MARGIN_UM + (h - 1 - y) * PIXEL_UM - inset
            rects.append(
                gdstk.rectangle(
                    (x0, y0),
                    (x0 + PIXEL_DRAW_UM, y0 + PIXEL_DRAW_UM),
                )
            )
            metal += 1

    if not rects:
        raise SystemExit("no opaque pixels found in PNG")

    # Merge into solid TopMetal1 polygons (critical for Magic TM1 DRC).
    merged = gdstk.boolean(
        rects,
        [],
        "or",
        layer=ART_LAYER,
        datatype=ART_DATATYPE,
    )
    for poly in merged:
        cell.add(poly)

    gds_path = OUT_DIR / f"{CELL_NAME}.gds"
    lef_path = OUT_DIR / f"{CELL_NAME}.lef"
    svg_path = OUT_DIR / f"{CELL_NAME}.svg"

    lib.write_gds(str(gds_path))
    write_lef(lef_path, CELL_NAME, width_um, height_um)
    cell.write_svg(str(svg_path))

    print(f"PNG:    {PNG_PATH} → {w}x{h} grid")
    print(
        f"metal:  {metal} pixels @ {PIXEL_UM} µm "
        f"(draw {PIXEL_DRAW_UM} µm, merged) → {width_um:.1f} x {height_um:.1f} µm"
    )
    print(f"polys:  {len(merged)}")
    print(f"wrote:  {gds_path}")
    print(f"        {lef_path}")
    print(f"        {svg_path}")


if __name__ == "__main__":
    main()
