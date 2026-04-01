# CarouselMaker

Paste slide content into Claude Code. Get a branded LinkedIn carousel PDF.

No manual design. No Figma skills required. No CLI to learn.

## Quickstart

```bash
git clone https://github.com/fern-opensource/carouselmaker.git
cd carouselmaker
```

1. Open the project in [Claude Code](https://claude.ai/code)
2. Connect Figma MCP — type `/mcp` and authenticate
3. Create a `.env` with your keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   FIGMA_ACCESS_TOKEN=figd_...
   ```
4. Tell Claude what you want:
   > "Generate a carousel about the three pillars of platform engineering"

That's it. Claude reads your `brand.json`, builds the slides in Figma, exports a PDF.

## Why Claude Code?

The Figma Plugin API — the only way to programmatically create design content on the canvas — requires MCP. The Figma REST API is read-only for visual elements. Claude Code is the runtime that bridges your content to Figma's canvas.

This isn't a workaround. It's the architecture:

```
You  -->  Claude Code  -->  Figma MCP  -->  Canvas  -->  PDF
             |                                           ^
             |  reads brand.json                         |
             |  extracts slide structure                 |
             |  generates Plugin API JavaScript          |
             |  exports via Figma REST API  -------------+
```

## Brand File

Your entire visual identity lives in `brand.json`. Swap the file, reskin every carousel.

```json
{
  "name": "Hot Pink Demo",
  "tagline": "A Demo Brand for Testing",
  "colors": {
    "bg_light": "#FFF0F5",
    "bg_dark": "#4A0028",
    "text_dark": "#4A0028",
    "text_light": "#FFF0F5",
    "text_muted": "#99004D",
    "accent": "#FF1493",
    "divider": "#FF1493"
  },
  "typography": {
    "font_heading": "Comic Neue",
    "font_body": "Comic Neue"
  },
  "layout": {
    "slide_w": 1080,
    "slide_h": 1080,
    "padding": 88,
    "corner_radius": 16
  },
  "figma": {
    "icon_library_file_key": "Io9LLV3Ny4Vb4LIB0G9LLy"
  }
}
```

A demo brand with [icon library](https://www.figma.com/design/Io9LLV3Ny4Vb4LIB0G9LLy) is included. Create your own `brand.json` with your colors, fonts, and a Figma icon library to make it yours.

## Icon Library

Vector icons live in a Figma file, referenced by `icon_library_file_key` in the brand file. During generation:

1. Claude picks an `icon_hint` based on slide content (e.g. `"shield"`, `"brain"`, `"workflow"`)
2. Queries the icon library file by label
3. Exports SVG path data from the matching node
4. Inserts the vector icon into the carousel frame

Generate your icon library with [Figma Make](https://www.figma.com/make) or design one manually. The pipeline just needs labeled frames with vector content.

## Architecture

The project provides structured models, brand loading, and content extraction that Claude Code uses during generation.

| Component | What It Does |
|-----------|-------------|
| `brand.json` | Colors, fonts, layout, icon library reference |
| `models.py` | `CarouselSlide`, `CarouselSpec` — Pydantic data models |
| `nodes/extract.py` | Claude API prompt for markdown → structured slide spec |
| `nodes/figma.py` | `load_brand()` + Figma instruction generation |
| `nodes/export.py` | Figma REST API PDF export + page merging |
| `graph.py` | LangGraph state machine (extract → figma → export) |

### CLI (optional)

A Click CLI is included for testing pipeline stages outside Claude Code:

```bash
uv venv && source .venv/bin/activate && uv pip install -e .

# Test API and brand file connections
carouselmaker health

# Extract slide structure from markdown
carouselmaker extract-only examples/agentic_taxonomy.md

# Extract + generate Figma instructions JSON
carouselmaker generate examples/agentic_taxonomy.md --brand brand.json
```

## Project Structure

```
carouselmaker/
  brand.json                  # Brand tokens — swap this to reskin
  .mcp.json                   # Figma MCP server config (auto-connects in Claude Code)
  .env.example                # API key template
  examples/
    agentic_taxonomy.md       # Example input content
    brand_hotpink.json        # Demo brand (Comic Neue + hot pink)
  src/carouselmaker/
    config.py                 # Settings (.env + brand file path)
    models.py                 # CarouselSlide, CarouselSpec
    cli.py                    # Click CLI (health, generate, extract-only)
    graph_carousel/
      state.py                # CarouselState TypedDict
      graph.py                # LangGraph pipeline
      nodes/
        extract.py            # Claude content extraction
        figma.py              # Brand loading + instruction generation
        export.py             # Figma REST API PDF export
```

## License

MIT
