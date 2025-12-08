import logging
import json
import os
from typing import Union, List, Dict, Any, Optional

# Suppress INFO messages from matplotlib
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Deferring imports to handle cases where they might not be installed
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False
    logging.warning("Pandas library not found. Data analysis tools will be limited.")

try:
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    train_test_split = None
    LinearRegression = None
    mean_squared_error = None
    r2_score = None
    np = None
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn library not found. Machine learning tools will be limited.")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    sns = None
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib or Seaborn not found. Visualization tools will be limited.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataAnalysisManager:
    """
    A comprehensive manager for loading, analyzing, and visualizing data.
    This manager holds a pandas DataFrame in state and provides a suite of methods
    for data manipulation, statistical analysis, machine learning, and visualization.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataAnalysisManager, cls).__new__(cls)
            if not PANDAS_AVAILABLE:
                logger.error("Pandas library is not installed. Data analysis manager will not function.")
                cls._instance.df = None
            else:
                cls._instance.df: Optional[pd.DataFrame] = None
        return cls._instance

    def _ensure_df_loaded(self) -> None:
        """Checks if a DataFrame is loaded, raising an error if not."""
        if self.df is None:
            raise ValueError("No data loaded. Please load data using 'load_data' before calling any analysis methods.")

    def load_data(self, data_source: Union[str, List[Dict[str, Any]], pd.DataFrame], file_type: str = "csv") -> str:
        """
        Loads data from various sources into the internal DataFrame.
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' library is not installed.")

        if isinstance(data_source, pd.DataFrame):
            self.df = data_source
        elif isinstance(data_source, list) and all(isinstance(i, dict) for i in data_source):
            self.df = pd.DataFrame(data_source)
        elif isinstance(data_source, str):
            if not os.path.exists(data_source):
                raise FileNotFoundError(f"The file '{data_source}' was not found.")
            
            if file_type.lower() == "csv":
                self.df = pd.read_csv(data_source)
            elif file_type.lower() == "json":
                self.df = pd.read_json(data_source)
            elif file_type.lower() == "excel":
                try:
                    self.df = pd.read_excel(data_source)
                except ImportError:
                    raise ImportError("To read Excel files, please install 'openpyxl' with 'pip install openpyxl'.")
            else:
                raise ValueError(f"Unsupported file type: {file_type}. Use 'csv', 'json', or 'excel'.")
        else:
            raise ValueError("Unsupported data source type. Provide a file path, list of dicts, or a pandas DataFrame.")
        
        return f"Data loaded successfully. Shape: {self.df.shape}, Columns: {list(self.df.columns)}"

    def get_info(self) -> Dict[str, Any]:
        """
        Retrieves concise information about the loaded DataFrame.

        Returns:
            A dictionary containing data types, non-null values, and memory usage.
        """
        self._ensure_df_loaded()
        info_dict = {
            "columns": self.df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "non_null_counts": self.df.count().to_dict(),
            "total_rows": len(self.df),
            "memory_usage": f"{self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        }
        return info_dict

    def describe_data(self) -> Dict[str, Any]:
        """
        Generates descriptive statistics for numerical columns.

        Returns:
            A dictionary of descriptive statistics (mean, std, etc.) for each numerical column.
        """
        self._ensure_df_loaded()
        return self.df.describe().to_dict()

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """
        Computes the pairwise correlation of numerical columns.

        Returns:
            A dictionary representing the correlation matrix.
        """
        self._ensure_df_loaded()
        numerical_df = self.df.select_dtypes(include=np.number)
        if numerical_df.shape[1] < 2:
            raise ValueError("Correlation matrix requires at least two numerical columns.")
        return numerical_df.corr().to_dict()

    def plot_histogram(self, column: str, save_path: str) -> str:
        """
        Generates and saves a histogram for a specified numerical column.

        Args:
            column: The numerical column to plot.
            save_path: The file path to save the histogram image (e.g., 'histogram.png').

        Returns:
            A confirmation message with the path to the saved plot.
        """
        self._ensure_df_loaded()
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Visualization libraries not installed. Please run 'pip install matplotlib seaborn'.")
        if column not in self.df.columns:
            raise KeyError(f"Column '{column}' not found in the DataFrame.")
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            raise TypeError(f"Column '{column}' must be of a numeric type to plot a histogram.")

        plt.figure(figsize=(10, 6))
        sns.histplot(self.df[column], kde=True)
        plt.title(f'Histogram of {column}', fontsize=16)
        plt.xlabel(column, fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.grid(axis='y', alpha=0.75)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        return f"Histogram saved to '{save_path}'"

    def plot_scatter(self, x_column: str, y_column: str, save_path: str) -> str:
        """
        Generates and saves a scatter plot for two specified numerical columns.

        Args:
            x_column: The column for the x-axis.
            y_column: The column for the y-axis.
            save_path: The file path to save the scatter plot image (e.g., 'scatter.png').

        Returns:
            A confirmation message with the path to the saved plot.
        """
        self._ensure_df_loaded()
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Visualization libraries not installed. Please run 'pip install matplotlib seaborn'.")
        for col in [x_column, y_column]:
            if col not in self.df.columns:
                raise KeyError(f"Column '{col}' not found in the DataFrame.")
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                raise TypeError(f"Column '{col}' must be of a numeric type for a scatter plot.")

        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=self.df[x_column], y=self.df[y_column])
        plt.title(f'Scatter Plot of {y_column} vs. {x_column}', fontsize=16)
        plt.xlabel(x_column, fontsize=12)
        plt.ylabel(y_column, fontsize=12)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        return f"Scatter plot saved to '{save_path}'"

    def plot_correlation_heatmap(self, save_path: str) -> str:
        """
        Generates and saves a heatmap of the correlation matrix for numerical columns.

        Args:
            save_path: The file path to save the heatmap image (e.g., 'heatmap.png').

        Returns:
            A confirmation message with the path to the saved plot.
        """
        self._ensure_df_loaded()
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Visualization libraries not installed. Please run 'pip install matplotlib seaborn'.")
        
        numerical_df = self.df.select_dtypes(include=np.number)
        if numerical_df.shape[1] < 2:
            raise ValueError("Correlation heatmap requires at least two numerical columns.")
            
        corr_matrix = numerical_df.corr()

        plt.figure(figsize=(12, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('Correlation Heatmap', fontsize=16)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        return f"Correlation heatmap saved to '{save_path}'"

    def perform_linear_regression(self, feature_columns: List[str], target_column: str) -> Dict[str, Any]:
        """
        Performs linear regression on specified feature and target columns.

        Returns:
            A dictionary containing the model coefficients, intercept, Mean Squared Error (MSE), and R-squared value.
        """
        self._ensure_df_loaded()
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn not installed. Please run 'pip install scikit-learn'.")
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas not installed. Please run 'pip install pandas'.")
        if not np:
            raise ImportError("Numpy not installed. Please run 'pip install numpy'.")

        for col in feature_columns + [target_column]:
            if col not in self.df.columns:
                raise KeyError(f"Column '{col}' not found in the DataFrame.")
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                raise TypeError(f"Column '{col}' must be of a numeric type for linear regression.")

        X = self.df[feature_columns]
        y = self.df[target_column]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        return {
            "coefficients": dict(zip(feature_columns, model.coef_)),
            "intercept": model.intercept_,
            "mean_squared_error": mse,
            "r_squared": r2
        }

data_analysis_manager = DataAnalysisManager()

class LoadDataTool(BaseTool):
    """Loads data into the data analysis manager."""
    def __init__(self, tool_name):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Loads data from various sources (CSV, JSON, Excel file path, list of dicts, or JSON string) into the data analysis manager's internal DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_source": {
                    "type": ["string", "array", "object"],
                    "description": "Path to a CSV, JSON, or Excel file, a list of dictionaries, or a JSON string representing the data."
                },
                "file_type": {"type": "string", "enum": ["csv", "json", "excel"], "default": "csv", "description": "The type of the file if data_source is a path."}
            },
            "required": ["data_source"]
        }

    def execute(self, data_source: Union[str, List[Dict[str, Any]], Any], file_type: str = "csv", **kwargs: Any) -> str:
        try:
            if isinstance(data_source, str) and (data_source.startswith('[') or data_source.startswith('{')):
                # Assume it's a JSON string if it starts with [ or {
                result = data_analysis_manager.load_data(json.loads(data_source), file_type)
            else:
                result = data_analysis_manager.load_data(data_source, file_type)
            return json.dumps({"message": result, "shape": list(data_analysis_manager.df.shape), "columns": data_analysis_manager.df.columns.tolist()}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to load data: {e}"})

class GetDataInfoTool(BaseTool):
    """Retrieves concise information about the loaded DataFrame."""
    def __init__(self, tool_name="get_data_info"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves concise information about the loaded DataFrame, including column names, data types, non-null counts, and memory usage."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        try:
            info = data_analysis_manager.get_info()
            return json.dumps(info, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get data info: {e}"})

class DescribeDataTool(BaseTool):
    """Generates descriptive statistics for numerical columns."""
    def __init__(self, tool_name="describe_data"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates descriptive statistics (mean, std, min, max, quartiles, etc.) for numerical columns in the loaded DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        try:
            description = data_analysis_manager.describe_data()
            return json.dumps(description, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to describe data: {e}"})

class GetCorrelationMatrixTool(BaseTool):
    """Computes the pairwise correlation of numerical columns."""
    def __init__(self, tool_name="get_correlation_matrix"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Computes the pairwise correlation of numerical columns in the loaded DataFrame, returning a correlation matrix."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        try:
            correlation_matrix = data_analysis_manager.get_correlation_matrix()
            return json.dumps(correlation_matrix, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get correlation matrix: {e}"})

class PlotHistogramTool(BaseTool):
    """Generates and saves a histogram for a specified numerical column."""
    def __init__(self, tool_name="plot_histogram"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates and saves a histogram for a specified numerical column in the loaded DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "The numerical column to plot."},
                "save_path": {"type": "string", "description": "The absolute file path to save the histogram image (e.g., 'path/to/histogram.png')."}
            },
            "required": ["column", "save_path"]
        }

    def execute(self, column: str, save_path: str, **kwargs: Any) -> str:
        try:
            result = data_analysis_manager.plot_histogram(column, save_path)
            return json.dumps({"message": result, "file_path": os.path.abspath(save_path)}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to plot histogram: {e}"})

class PlotScatterTool(BaseTool):
    """Generates and saves a scatter plot for two specified numerical columns."""
    def __init__(self, tool_name="plot_scatter"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates and saves a scatter plot for two specified numerical columns in the loaded DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "x_column": {"type": "string", "description": "The column for the x-axis."},
                "y_column": {"type": "string", "description": "The column for the y-axis."},
                "save_path": {"type": "string", "description": "The absolute file path to save the scatter plot image (e.g., 'path/to/scatter.png')."}
            },
            "required": ["x_column", "y_column", "save_path"]
        }

    def execute(self, x_column: str, y_column: str, save_path: str, **kwargs: Any) -> str:
        try:
            result = data_analysis_manager.plot_scatter(x_column, y_column, save_path)
            return json.dumps({"message": result, "file_path": os.path.abspath(save_path)}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to plot scatter plot: {e}"})

class PlotCorrelationHeatmapTool(BaseTool):
    """Generates and saves a heatmap of the correlation matrix for numerical columns."""
    def __init__(self, tool_name="plot_correlation_heatmap"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates and saves a heatmap of the correlation matrix for numerical columns in the loaded DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "save_path": {"type": "string", "description": "The absolute file path to save the heatmap image (e.g., 'path/to/heatmap.png')."}
            },
            "required": ["save_path"]
        }

    def execute(self, save_path: str, **kwargs: Any) -> str:
        try:
            result = data_analysis_manager.plot_correlation_heatmap(save_path)
            return json.dumps({"message": result, "file_path": os.path.abspath(save_path)}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to plot correlation heatmap: {e}"})

class PerformLinearRegressionTool(BaseTool):
    """Performs linear regression on specified feature and target columns."""
    def __init__(self, tool_name="perform_linear_regression"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Performs linear regression on specified feature and target columns in the loaded DataFrame."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feature_columns": {"type": "array", "items": {"type": "string"}, "description": "A list of column names to be used as features (X)."},
                "target_column": {"type": "string", "description": "The column name to be used as the target (y)."}
            },
            "required": ["feature_columns", "target_column"]
        }

    def execute(self, feature_columns: List[str], target_column: str, **kwargs: Any) -> str:
        try:
            results = data_analysis_manager.perform_linear_regression(feature_columns, target_column)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to perform linear regression: {e}"})
