import polars as pl
import matplotlib.pyplot as plt
import matplotlib.patches as patches

with open("hexcode_rl.csv", 'r') as runninglist:
    hexcodes_rl = pl.read_csv(runninglist).rename({"color": "hexcodes_manual"})

with open("parsed_hexcodes.csv", 'r') as parsed:
    hexcodes_parsed = pl.read_csv(parsed).rename({"color": "hexcodes_parsed"})

hexcodes_diff = hexcodes_parsed.join(
    hexcodes_rl,
    on = "variant",
    how = "left"
).filter(
    pl.col("hexcodes_parsed").str.to_lowercase().str.strip_chars() != pl.col("hexcodes_manual").str.to_lowercase().str.strip_chars()
    )


def plot_colors_from_polars_df(df: pl.DataFrame, label_col: str, color_col1: str, color_col2: str):
    """
    Plots two color hex codes from a Polars DataFrame side by side.

    Args:
        df: The Polars DataFrame.
        label_col: The name of the label column.
        color_col1: The name of the first color column (hex codes).
        color_col2: The name of the second color column (hex codes).
    """
    num_rows = len(df)
    # Set up the figure and axes
    fig, ax = plt.subplots(figsize=(8, num_rows * 0.5)) # Adjust figure size based on number of rows
    
    # Iterate over each row and plot the two colors as rectangles
    for i, row in enumerate(df.iter_rows(named=True)):
        label = row[label_col]
        color1 = row[color_col1]
        color2 = row[color_col2]
        
        # Plot the first color (left side)
        rect1 = patches.Rectangle((0, i), 0.5, 1, color=color1, transform=ax.transData)
        ax.add_patch(rect1)
        
        # Plot the second color (right side)
        rect2 = patches.Rectangle((0.5, i), 0.5, 1, color=color2, transform=ax.transData)
        ax.add_patch(rect2)
        
        # Add the label
        ax.text(1.05, i + 0.5, label, va='center', fontsize=12)
        
    # Configure the plot
    ax.set_xlim(0, 2) # Adjust x-limit to accommodate labels
    ax.set_ylim(0, num_rows)
    ax.set_yticks([]) # Hide y-axis ticks as we have labels
    ax.set_xticks([]) # Hide x-axis ticks
    ax.set_title("Side-by-Side Color Comparison")
    
    # Add column headers
    ax.text(0.25, num_rows, color_col1, ha='center', va='bottom', fontsize=12)
    ax.text(0.75, num_rows, color_col2, ha='center', va='bottom', fontsize=12)
    
    plt.show()

print(hexcodes_diff)
plot_colors_from_polars_df(hexcodes_diff,
                           label_col="variant",
                           color_col1="hexcodes_parsed",
                           color_col2="hexcodes_manual")

