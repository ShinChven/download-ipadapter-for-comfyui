# Adding Default Model Sources

This guide is for project maintainers who want to add new default model sources to the `comfydl` package.

## Overview

Default model sources are YAML files bundled with the `comfydl` package. They provide the "built-in" recipes that all users can access immediately (e.g., `comfydl flux`).

## Location

All default source files must be placed in the `comfydl/model_sources/` directory.

```bash
comfydl/model_sources/
├── flux.yaml
├── ipadapters.yaml
├── your_new_source.yaml  <-- Add new files here
└── ...
```

## Creating a New Source

1.  **Create a YAML file**: Choose a short, descriptive filename (e.g., `realvis.yaml`). The filename (without extension) will be the command used to invoke it (e.g., `comfydl realvis`).

2.  **Define Content**:
    Use the following structure:

    ```yaml
    description: "Brief description of the model set"
    source: "URL to the model's homepage or documentation (optional but recommended)"
    downloads:
      - url: "https://huggingface.co/..."
        dest: "models/checkpoints/filename.safetensors"
      - url: "https://civitai.com/api/download/models/..."
        dest: "models/loras/filename.safetensors"
    ```

    *   **dest**: relative path from the ComfyUI root.

3.  **Civitai Links**:
    *   Use the API download link: `https://civitai.com/api/download/models/ID`
    *   Do **not** include the token in the URL. `comfydl` handles appending the user's token automatically.

## Testing

Before committing, test your new source locally:

1.  Ensure you have your development environment set up.
2.  Run `comfydl` pointing to your new file or by name if you are in the project root.

    ```bash
    # Test by filename
    python -m comfydl.main your_new_source_name /tmp/test_download
    ```
    *   This will attempt to download the files to `/tmp/test_download`.
    *   Verify that files land in the correct subdirectories (e.g., `/tmp/test_download/models/checkpoints/...`).

