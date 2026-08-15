import os
import re
import shutil

# Paths
posts_dir = "/Users/dirac042/Desktop/dirac042/content/posts/"
attachments_dir = "/Users/dirac042/Documents/dirac042/Images"
static_images_dir = "/Users/dirac042/Desktop/dirac042/static/images"

# Step 1: Process each markdown file in the posts directory
for filename in os.listdir(posts_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(posts_dir, filename)

        with open(filepath, "r") as file:
            content = file.read()

        # Step 2: Find all Obsidian image embeds: [[img.png]], ![[img.png]], [[img.jpg|300]]
        #         (png / jpg / jpeg / gif / webp / svg — case-insensitive)
        pattern = re.compile(
            r"!?\[\[([^\]|]*\.(?:png|jpe?g|gif|webp|svg))(?:\|[^\]]*)?\]\]", re.IGNORECASE
        )
        images = pattern.findall(content)

        # Step 3: Replace image links and ensure URLs are correctly formatted
        def to_markdown(match):
            image = match.group(1)
            # Prepare the Markdown-compatible link with %20 replacing spaces
            return f"![Image Description](/images/{image.replace(' ', '%20')})"

        content = pattern.sub(to_markdown, content)

        for image in images:
            # Step 4: Copy the image to the Hugo static/images directory if it exists
            image_source = os.path.join(attachments_dir, image)
            if os.path.exists(image_source):
                shutil.copy(image_source, static_images_dir)

        # Step 5: Write the updated content back to the markdown file
        with open(filepath, "w") as file:
            file.write(content)

print("Markdown files processed and images copied successfully.")
