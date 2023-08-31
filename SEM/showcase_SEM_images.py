# %%
import re
import os
from bix_analysis_libraries import thot as bt

# %%
db = bt.init_thot(__file__)

# %%
files = os.listdir("converted")

# %%
current_path = os.getcwd()
batch_path = os.path.dirname(current_path)
folder_name = os.path.basename(batch_path)
markdown_file_name = f"{folder_name}.md"
markdown_file_path = os.path.join(batch_path, markdown_file_name)
markdown_file_path
# %%
for file in files:
    # Read the markdown file
    with open(markdown_file_path, "r") as note:
        content = note.read()

    # Check if the text is present
    if file not in content:
        # Find the line "### SEM"
        match = re.search(r"### SEM", content)

        if match:
            # Insert the text after the line "### SEM"
            insertion_point = match.end()
            updated_content = (
                content[:insertion_point]
                + f"\n![[{file}|450]]\n"
                + content[insertion_point:]
            )

        # Write the updated content back to the file
        with open(markdown_file_path, "w") as note:
            note.write(updated_content)
