# File-level recipes for Illustrator assets

Use this reference when `.ai` files are PDF-compatible or when Illustrator is not installed.

## Inspect

```bash
file -b asset.ai
pdfinfo asset.ai
```

If `file` reports PDF data or `pdfinfo` works, the asset can usually be rendered without Illustrator.

## Render pages to PNG

```bash
mkdir -p out
pdftocairo -png -r 150 asset.ai out/page
```

Use 150 dpi for review boards and 300 dpi for closer inspection. For huge brandbooks, render only the pages needed.

## Render one page

```bash
pdftocairo -png -r 200 -f 1 -l 1 asset.ai out/page
```

## Try SVG extraction

```bash
pdftocairo -svg -f 1 -l 1 asset.ai out/page-01.svg
```

SVG output can preserve some vector information, but it is not proof that the original Illustrator layers remain editable.

## Contact sheets

After rendering pages, use ImageMagick if available:

```bash
magick montage out/page-*.png -tile 4x -geometry 420x420+16+16 contact.png
```

If ImageMagick is unavailable, create an HTML review board with image thumbnails instead.

## Proof wording

Use precise claims:

- `rendered from PDF-compatible AI`
- `visual review export exists`
- `page count read through pdfinfo`

Avoid stronger claims unless proved:

- `native Illustrator layers are editable`
- `fonts are available`
- `vectors imported cleanly`
