# Catalogues Directory

This directory is used for **optional caching** of faction catalogues downloaded from [BSData/wh40k-10e](https://github.com/BSData/wh40k-10e).

## How It Works

### In-Memory Processing (Default)
By default, the application:
1. Downloads `.cat` files from BSData GitHub
2. Parses them to Python dictionaries **in-memory**
3. Uses them to generate cheat sheets
4. **No disk writes** - catalogues are not saved

This approach:
- ✅ Saves disk space on web servers
- ✅ Always uses latest data from BSData
- ✅ Stateless - perfect for containers/cloud deployment

### Optional Local Caching
If `.yaml` files exist in this directory, they will be used for faster processing:
- If a `.yaml` file exists → loaded from disk (fast)
- If not → downloaded and parsed in-memory (slower, but no disk write)

This is useful for local development but **not required** for production deployment.

## For Production Deployment

You can safely:
- ✅ Delete all `.yaml` files (catalogues downloaded on-demand)
- ✅ Delete the entire `catalogues/` directory (auto-created if needed)
- ✅ Add `catalogues/*.yaml` to `.gitignore` (already done)

The application will automatically download and parse catalogues as users request different factions, without filling up disk space.

## Supported Factions

All Warhammer 40k 10th Edition factions from BSData are supported, including:
- **Chaos**: Death Guard, Thousand Sons, World Eaters, Chaos Space Marines, etc.
- **Imperium**: Space Marines (all chapters), Astra Militarum, Adeptus Custodes, etc.
- **Xenos**: Necrons, Orks, Tyranids, T'au Empire, Aeldari, Drukhari, etc.

Catalogues are fetched directly from the official [BSData/wh40k-10e](https://github.com/BSData/wh40k-10e) repository.
