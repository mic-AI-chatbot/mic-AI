import logging
import os
import json
import shutil
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

# Suppress INFO messages from matplotlib and seaborn
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('seaborn').setLevel(logging.WARNING)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    sns = None
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataVisualizationTool(BaseTool):
    """
    A comprehensive tool for generating various data visualizations (line, bar, scatter,
    histogram, box, pie, heatmap, violin, KDE plots).
    """

    def __init__(self, tool_name: str = "data_visualization_tool"):
        super().__init__(tool_name)
        self._ensure_libs_available()

    @property
    def description(self) -> str:
        return "Generates various data visualizations (line, bar, scatter, histogram, box, pie, heatmap, violin, KDE plots) from data sources."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plot_type": {
                    "type": "string",
                    "description": "The type of plot to generate.",
                    "enum": ["line", "bar", "scatter", "histogram", "box", "pie", "heatmap", "violin", "kde"]
                },
                "data_source": {
                    "type": ["string", "array", "object"], # File path, list of dicts, or DataFrame (as JSON string)
                    "description": "The data source (file path, JSON string of list of dicts, or JSON string of DataFrame)."
                },
                "output_path": {
                    "type": "string",
                    "description": "The absolute path to save the generated plot image."
                },
                "x_column": {"type": "string", "description": "Column for the x-axis."},
                "y_column": {"type": "string", "description": "Column for the y-axis."},
                "labels_column": {"type": "string", "description": "Column for pie chart labels."},
                "values_column": {"type": "string", "description": "Column for pie chart values."},
                "title": {"type": "string", "description": "Optional title for the plot."},
                "xlabel": {"type": "string", "description": "Optional label for the x-axis."},
                "ylabel": {"type": "string", "description": "Optional label for the y-axis."},
                "figsize_width": {"type": "integer", "default": 10},
                "figsize_height": {"type": "integer", "default": 6}
            },
            "required": ["plot_type", "data_source", "output_path"]
        }

    def _ensure_libs_available(self) -> None:
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' library is not installed. Please install it with 'pip install pandas'.")
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("The 'matplotlib' and 'seaborn' libraries are not installed. Please install them with 'pip install matplotlib seaborn'.")

    def _load_data(self, data_source: Union[str, List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
        if isinstance(data_source, pd.DataFrame): return data_source
        elif isinstance(data_source, list) and all(isinstance(i, dict) for i in data_source): return pd.DataFrame(data_source)
        elif isinstance(data_source, str):
            if os.path.exists(data_source):
                if data_source.lower().endswith('.csv'): return pd.read_csv(data_source)
                elif data_source.lower().endswith('.json'): return pd.read_json(data_source)
                else: raise ValueError("Unsupported data source file type. Use .csv or .json.")
            else:
                try: return pd.DataFrame(json.loads(data_source))
                except json.JSONDecodeError: raise ValueError("'data_source' is not a valid file path, JSON string, or DataFrame.")
        else: raise ValueError("Unsupported data source type.")

    def _save_plot(self, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return f"Plot saved to '{output_path}'."

    def _line_plot(self, df: pd.DataFrame, x_column: str, y_column: str, output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns or y_column not in df.columns: raise KeyError(f"One or both columns ('{x_column}', '{y_column}') not found in data.")
        plt.figure(figsize=figsize); sns.lineplot(x=df[x_column], y=df[y_column])
        plt.title(title if title else f"Line Plot of {y_column} vs. {x_column}"); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column)
        return self._save_plot(output_path)

    def _bar_plot(self, df: pd.DataFrame, x_column: str, y_column: str, output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns or y_column not in df.columns: raise KeyError(f"One or both columns ('{x_column}', '{y_column}') not found in data.")
        plt.figure(figsize=figsize); sns.barplot(x=df[x_column], y=df[y_column])
        plt.title(title if title else f"Bar Plot of {y_column} by {x_column}"); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column)
        return self._save_plot(output_path)

    def _scatter_plot(self, df: pd.DataFrame, x_column: str, y_column: str, output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns or y_column not in df.columns: raise KeyError(f"One or both columns ('{x_column}', '{y_column}') not found in data.")
        plt.figure(figsize=figsize); sns.scatterplot(x=df[x_column], y=df[y_column])
        plt.title(title if title else f"Scatter Plot of {y_column} vs. {x_column}"); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column)
        return self._save_plot(output_path)

    def _histogram(self, df: pd.DataFrame, x_column: str, output_path: str, title: Optional[str], xlabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns: raise KeyError(f"Column '{x_column}' not found in data.")
        if not pd.api.types.is_numeric_dtype(df[x_column]): raise TypeError(f"Column '{x_column}' must be numerical for a histogram.")
        plt.figure(figsize=figsize); sns.histplot(x=df[x_column], kde=True)
        plt.title(title if title else f"Histogram of {x_column}"); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel("Frequency")
        return self._save_plot(output_path)

    def _box_plot(self, df: pd.DataFrame, x_column: str, y_column: Optional[str], output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns: raise KeyError(f"Column '{x_column}' not found in data.")
        if y_column and y_column not in df.columns: raise KeyError(f"Column '{y_column}' not found in data.")
        plt.figure(figsize=figsize); sns.boxplot(x=df[x_column], y=df[y_column] if y_column else None)
        plt.title(title if title else (f"Box Plot of {y_column} by {x_column}" if y_column else f"Box Plot of {x_column}")); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column if y_column else "")
        return self._save_plot(output_path)

    def _pie_chart(self, df: pd.DataFrame, labels_column: str, values_column: str, output_path: str, title: Optional[str], figsize: tuple) -> str:
        if labels_column not in df.columns or values_column not in df.columns: raise KeyError(f"One or both columns ('{labels_column}', '{values_column}') not found in data.")
        plt.figure(figsize=figsize); plt.pie(df[values_column], labels=df[labels_column], autopct='%1.1f%%', startangle=90)
        plt.title(title if title else f"Pie Chart of {values_column} by {labels_column}"); plt.axis('equal')
        return self._save_plot(output_path)

    def _heatmap(self, df: pd.DataFrame, output_path: str, title: Optional[str], figsize: tuple) -> str:
        numerical_df = df.select_dtypes(include=['number'])
        if numerical_df.empty: raise ValueError("No numerical columns found for heatmap generation.")
        plt.figure(figsize=figsize); sns.heatmap(numerical_df.corr(), annot=True, fmt=".2f", cmap="viridis")
        plt.title(title if title else "Correlation Heatmap")
        return self._save_plot(output_path)

    def _violin_plot(self, df: pd.DataFrame, x_column: str, y_column: Optional[str], output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns: raise KeyError(f"Column '{x_column}' not found in data.")
        if y_column and y_column not in df.columns: raise KeyError(f"Column '{y_column}' not found in data.")
        plt.figure(figsize=figsize); sns.violinplot(x=df[x_column], y=df[y_column] if y_column else None)
        plt.title(title if title else (f"Violin Plot of {y_column} by {x_column}" if y_column else f"Violin Plot of {x_column}")); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column if y_column else "")
        return self._save_plot(output_path)

    def _kde_plot(self, df: pd.DataFrame, x_column: str, y_column: Optional[str], output_path: str, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str], figsize: tuple) -> str:
        if x_column not in df.columns: raise KeyError(f"Column '{x_column}' not found in data.")
        if y_column and y_column not in df.columns: raise KeyError(f"Column '{y_column}' not found in data.")
        plt.figure(figsize=figsize); sns.kdeplot(x=df[x_column], y=df[y_column] if y_column else None, fill=True)
        plt.title(title if title else (f"KDE Plot of {y_column} vs. {x_column}" if y_column else f"KDE Plot of {x_column}")); plt.xlabel(xlabel if xlabel else x_column); plt.ylabel(ylabel if ylabel else y_column if y_column else "Density")
        return self._save_plot(output_path)

    def execute(self, plot_type: str, data_source: Union[str, List[Dict[str, Any]], pd.DataFrame], output_path: str, **kwargs: Any) -> str:
        df = self._load_data(data_source)
        figsize = (kwargs.get("figsize_width", 10), kwargs.get("figsize_height", 6))
        
        if plot_type == "line":
            return self._line_plot(df, kwargs["x_column"], kwargs["y_column"], output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        elif plot_type == "bar":
            return self._bar_plot(df, kwargs["x_column"], kwargs["y_column"], output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        elif plot_type == "scatter":
            return self._scatter_plot(df, kwargs["x_column"], kwargs["y_column"], output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        elif plot_type == "histogram":
            return self._histogram(df, kwargs["x_column"], output_path, kwargs.get("title"), kwargs.get("xlabel"), figsize)
        elif plot_type == "box":
            return self._box_plot(df, kwargs["x_column"], kwargs.get("y_column"), output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        elif plot_type == "pie":
            return self._pie_chart(df, kwargs["labels_column"], kwargs["values_column"], output_path, kwargs.get("title"), figsize)
        elif plot_type == "heatmap":
            return self._heatmap(df, output_path, kwargs.get("title"), figsize)
        elif plot_type == "violin":
            return self._violin_plot(df, kwargs["x_column"], kwargs.get("y_column"), output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        elif plot_type == "kde":
            return self._kde_plot(df, kwargs["x_column"], kwargs.get("y_column"), output_path, kwargs.get("title"), kwargs.get("xlabel"), kwargs.get("ylabel"), figsize)
        else:
            raise ValueError(f"Unsupported plot type: {plot_type}")

if __name__ == '__main__':
    print("Demonstrating DataVisualizationTool functionality...")
    tool = DataVisualizationTool()
    
    test_data_path = "test_visualization_data.csv"
    output_dir = "generated_plots"

    try:
        os.makedirs(output_dir, exist_ok=True)
        dummy_data = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C'],
            'value': [10, 15, 12, 20, 18, 9, 25, 13, 11, 22],
            'sales': [100, 150, 120, 200, 180, 90, 250, 130, 110, 220],
            'profit': [10, 20, 15, 30, 25, 10, 35, 18, 12, 28]
        })
        dummy_data.to_csv(test_data_path, index=False)

        print("\n--- Generating Line Plot ---")
        tool.execute(plot_type="line", data_source=test_data_path, output_path=os.path.join(output_dir, 'line_plot.png'), x_column='value', y_column='sales', title="Value vs Sales")
        
        print("\n--- Generating Bar Plot ---")
        tool.execute(plot_type="bar", data_source=test_data_path, output_path=os.path.join(output_dir, 'bar_plot.png'), x_column='category', y_column='sales', title="Sales by Category")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(test_data_path): os.remove(test_data_path)
        if os.path.exists(output_dir): shutil.rmtree(output_dir)
        print("\nCleanup complete.")