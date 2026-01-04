# Multi Project Canvas

A QGIS plugin for managing multiple projects simultaneously in a single QGIS instance.

![QGIS Version](https://img.shields.io/badge/QGIS-3.16%2B-green.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)
![Version](https://img.shields.io/badge/Version-7.0.0-orange.svg)

## Overview

Multi Project Canvas allows you to work with multiple QGIS projects at the same time without opening separate QGIS instances. Each project is fully isolated with its own layers, extent, CRS, and bookmarks. Switch between projects with a single click while keeping all your work organized in one place.

## Features

### 📁 Multiple Projects Management
- Open and manage multiple QGIS projects in a single session
- Each project maintains its own layers, styles, and settings
- Quick switching between projects with automatic state saving
- Drag & drop to reorder projects in the list

### 📷 Map Thumbnails
- Live thumbnail preview for each project
- Visual identification of projects at a glance
- Auto-updates when project content changes
- Toggle thumbnails on/off to save space

### 🔖 Bookmarks
- Save spatial bookmarks per project
- Quick navigation to saved locations
- Collapsible bookmark panel
- Resizable section with splitter

### ⏪ Navigation History
- Back/Forward navigation for map extents
- Up to 50 positions stored per project
- Navigate through your exploration history
- Independent history for each project

### 🔄 Extent Synchronization
- Sync current extent to all projects
- Useful for comparing the same area across projects
- One-click synchronization

### 🔍 Global Search
- Search layers across all open projects
- Search in bookmark names
- Click results to switch project and select layer
- Real-time search as you type

### 🌍 Internationalization
- English (default)
- Italian (automatic detection based on QGIS locale)

## Installation

### From ZIP file
1. Download the latest release ZIP file
2. In QGIS, go to `Plugins` → `Manage and Install Plugins`
3. Click `Install from ZIP`
4. Select the downloaded ZIP file
5. Click `Install Plugin`

### Manual Installation
1. Extract the ZIP file
2. Copy the `multi_project_canvas_v7` folder to your QGIS plugins directory:
   - **Windows:** `C:\Users\{username}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin in `Plugins` → `Manage and Install Plugins`

## Usage

### Activating the Plugin
- Click the **Multi Project Panel** button in the toolbar, or
- Use the keyboard shortcut `Ctrl+Shift+P`, or
- Go to `Plugins` → `Multi Project Canvas` → `Multi Project Panel`

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Toggle the Multi Project panel |
| `Ctrl+T` | Create a new empty project |
| `Ctrl+Shift+O` | Open an existing project in a new tab |

### Panel Layout

```
┌─────────────────────────────┐
│ PROJECTS    [👁] [+] [📂]   │  Header with actions
├─────────────────────────────┤
│ 🔍 Search layers...         │  Global search
├─────────────────────────────┤
│ ┌─────┐ Project 1           │
│ │ 🗺️  │ 5 layers • 2 bm     │  Project with thumbnail
│ └─────┘ project.qgz         │
├─────────────────────────────┤
│ ┌─────┐ Project 2 •         │  • = unsaved changes
│ │     │ 3 layers            │
│ └─────┘ Not saved           │
├═════════════════════════════┤  ← Resizable splitter
│ ▶ Bookmarks            [+] 2│  Collapsible section
├─────────────────────────────┤
│ [◀] [▶] | [Sync]       [🔖]│  Navigation bar
├─────────────────────────────┤
│ [Save] [Save as]        [⚙] │  Footer actions
└─────────────────────────────┘
```

### Working with Projects

#### Creating a New Project
1. Click the `+` button in the header, or press `Ctrl+T`
2. A new empty project is created and activated
3. Add layers and configure as needed

#### Opening an Existing Project
1. Click the folder icon in the header, or press `Ctrl+Shift+O`
2. Select a `.qgs` or `.qgz` file
3. The project opens in a new tab

#### Switching Projects
- **Single click** on a project in the list to switch to it
- The current project state is automatically saved before switching
- All Processing tools, sketchy, and editing work on the active project

#### Renaming Projects
- **Double-click** on a project name to rename it
- Or right-click and select "Rename..."

#### Reordering Projects
- **Drag and drop** projects in the list to reorder
- Or right-click and use "Move up" / "Move down"

#### Saving Projects
- Click **Save** to save to the current file (or prompt for location if new)
- Click **Save as** to save with a new name/location
- Projects with unsaved changes show an orange dot indicator

#### Closing Projects
- Click the project's context menu (right-click) → "Close"
- You'll be prompted to save if there are unsaved changes
- The last project cannot be closed

### Working with Bookmarks

#### Adding a Bookmark
1. Navigate to the desired map extent
2. Click the bookmark icon (🔖) in the navigation bar
3. Enter a name for the bookmark
4. The bookmark is saved for the current project

#### Using Bookmarks
1. Expand the "Bookmarks" section (click the arrow)
2. **Double-click** a bookmark to zoom to that extent
3. Right-click for rename/delete options

#### Managing the Bookmarks Panel
- Click the section header to expand/collapse
- Drag the splitter handle to resize the section
- Bookmarks are saved per-project

### Navigation History

The plugin tracks your map navigation within each project:

- **Back button (◀)**: Return to the previous extent
- **Forward button (▶)**: Go to the next extent (after going back)
- Each project has its own independent history
- Up to 50 positions are stored per project

### Extent Synchronization

To apply the current map extent to all other projects:

1. Navigate to your desired extent
2. Click the **Sync** button in the navigation bar
3. All other projects will be updated to show the same area

This is useful when comparing the same geographic area across different projects.

### Searching

The search box allows you to find content across all open projects:

1. Type at least 2 characters to start searching
2. Results show matching:
   - Project names
   - Layer names
   - Bookmark names
3. Click a result to:
   - Switch to that project
   - Select the layer (if it's a layer result)
   - Zoom to the bookmark (if it's a bookmark result)

### Workspaces

Save and restore your entire multi-project session:

#### Saving a Workspace
1. Click the options menu (⚙) → "Save workspace..."
2. Choose a location and filename (`.mpw` extension)
3. All projects and their states are saved

#### Loading a Workspace
1. Click the options menu (⚙) → "Load workspace..."
2. Select a `.mpw` file
3. All projects from the workspace are restored

**Note:** Workspace files create a companion folder (`{name}_projects/`) containing the actual project files.

## Configuration

### Thumbnail Display
- Toggle the eye icon (👁) in the header to show/hide thumbnails
- Hiding thumbnails creates a more compact list

### Panel Position
- The panel can be docked on the left or right side of QGIS
- Drag the panel title bar to reposition

## Technical Details

### How It Works
- Each project is saved to a temporary `.qgz` file when switching
- The global `QgsProject.instance()` is cleared and reloaded on switch
- This ensures full compatibility with all QGIS tools and plugins
- Temporary files are cleaned up when the plugin is deactivated

### Performance Considerations
- Thumbnail generation happens on project save/switch
- Large projects may take a moment to switch
- Search reads project files to find layers

### Limitations
- Projects share the same plugin configurations
- Print layouts are tied to their respective projects
- Very large projects (many layers) may have slower switch times

## Troubleshooting

### Plugin doesn't appear after installation
1. Check that the plugin is enabled in Plugin Manager
2. Verify the folder name is correct in the plugins directory
3. Check the QGIS message log for errors

### Projects not saving correctly
1. Ensure you have write permissions to the save location
2. Check available disk space
3. Try "Save as" to a different location

### Thumbnails not showing
1. Verify the project has visible layers
2. Click options menu → "Refresh thumbnail"
3. Check that thumbnails are enabled (eye icon)

### Language not changing
- The plugin detects QGIS locale on startup
- Restart QGIS after changing language settings

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Setup
1. Clone the repository to your QGIS plugins folder
2. Enable the plugin in QGIS
3. Use the Plugin Reloader plugin for development

### Adding Translations
To add a new language:
1. Open `multi_project_canvas.py`
2. Find the `Sketchy` class with `_translations` dictionary
3. Add a new language code key (e.g., `'de'`, `'fr'`, `'es'`)
4. Add all translated strings

## License

This plugin is released under the GNU General Public License v3.0.

## Changelog

### Version 7.0.0
- Full internationalization support (English/Italian)
- Automatic language detection from QGIS settings
- Collapsible and resizable bookmark section
- Improved splitter for panel resizing

### Version 6.0.0
- Map thumbnails for visual project identification
- Per-project bookmarks
- Navigation history (back/forward)
- Extent synchronization across projects
- Global search for layers and bookmarks
- Drag & drop project reordering
- Double-click to rename

### Version 5.0.0
- Initial release with DockWidget interface
- Multiple project management
- Project save/load functionality
- Workspace save/load

## Credits

Developed by Federico

## Support

For bug reports and feature requests, please use the GitHub issue tracker.
