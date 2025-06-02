import numpy as np
import pandas as pd
import json
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn imports
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, 
    RandomizedSearchCV, StratifiedKFold
)
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    GradientBoostingRegressor, GradientBoostingClassifier,
    VotingRegressor, VotingClassifier
)
from sklearn.linear_model import (
    LinearRegression, Ridge, Lasso, ElasticNet,
    LogisticRegression
)
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieRecommendationTrainer:
    """
    Comprehensive ML model trainer for movie recommendation system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize trainer with configuration"""
        self.config = config or self._get_default_config()
        
        # Initialize models
        self.models = {}
        self.trained_models = {}
        self.model_scores = {}
        self.best_model = None
        self.best_model_name = None
        
        # Initialize preprocessors
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.pca = None
        
        # Training data
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = []
        
        # Results storage
        self.training_results = {}
        self.cv_results = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default training configuration"""
        return {
            'target_column': 'rating',
            'test_size': 0.2,
            'random_state': 42,
            'cv_folds': 5,
            'scoring_metric': 'neg_mean_squared_error',
            'feature_selection': {
                'enabled': True,
                'method': 'selectkbest',
                'k': 50
            },
            'dimensionality_reduction': {
                'enabled': False,
                'method': 'pca',
                'n_components': 0.95
            },
            'hyperparameter_tuning': {
                'enabled': True,
                'method': 'randomized',  # 'grid' or 'randomized'
                'n_iter': 50,
                'cv_folds': 3
            },
            'ensemble_methods': {
                'enabled': True,
                'voting_type': 'soft'  # 'soft' or 'hard'
            },
            'model_types': [
                'random_forest', 'gradient_boosting', 'knn', 
                'linear_regression', 'ridge', 'mlp'
            ],
            'save_models': True,
            'model_dir': 'models'
        }
    
    def initialize_models(self) -> Dict[str, Any]:
        """Initialize all ML models with default parameters"""
        logger.info("Initializing ML models...")
        
        models = {
            # Regression models
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0, random_state=self.config['random_state']),
            'lasso': Lasso(alpha=1.0, random_state=self.config['random_state']),
            'elastic_net': ElasticNet(alpha=1.0, random_state=self.config['random_state']),
            
            # Tree-based models
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                random_state=self.config['random_state'],
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                random_state=self.config['random_state']
            ),
            'decision_tree': DecisionTreeRegressor(
                random_state=self.config['random_state']
            ),
            
            # Instance-based models
            'knn': KNeighborsRegressor(n_neighbors=5),
            
            # SVM models
            'svr': SVR(kernel='rbf', C=1.0),
            
            # Neural networks
            'mlp': MLPRegressor(
                hidden_layer_sizes=(100, 50),
                random_state=self.config['random_state'],
                max_iter=500
            )
        }
        
        # Filter models based on config
        if 'model_types' in self.config:
            models = {k: v for k, v in models.items() if k in self.config['model_types']}
        
        self.models = models
        logger.info(f"Initialized {len(models)} models: {list(models.keys())}")
        
        return models
    
    def prepare_data(self, df: pd.DataFrame, target_column: str = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare data for training"""
        logger.info("Preparing data for training...")
        
        target_col = target_column or self.config['target_column']
        
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe")
        
        # Separate features and target
        y = df[target_col].values
        
        # Select numerical features for ML
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove target and non-feature columns
        exclude_cols = [
            target_col, 'title', 'description', 'imdb_id', 'poster_url',
            'genre', 'actors', 'director', 'language', 'country', 'mpaa_rating',
            'tags', 'tags_processed', 'tags_string', 'combined_text'
        ]
        
        feature_cols = [col for col in numerical_cols if col not in exclude_cols]
        
        if not feature_cols:
            raise ValueError("No numerical features found for training")
        
        X = df[feature_cols].fillna(0).values
        self.feature_names = feature_cols
        
        logger.info(f"Prepared data: {X.shape[0]} samples, {X.shape[1]} features")
        logger.info(f"Target range: {y.min():.2f} - {y.max():.2f}")
        
        return X, y, feature_cols
    
    def split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into training and testing sets"""
        logger.info(f"Splitting data with test_size={self.config['test_size']}")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config['test_size'],
            random_state=self.config['random_state'],
            stratify=None  # Can add stratification if needed
        )
        
        # Store splits
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        return X_train, X_test, y_train, y_test
    
    def preprocess_features(self, X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply feature preprocessing"""
        logger.info("Preprocessing features...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Feature selection
        if self.config['feature_selection']['enabled']:
            logger.info("Applying feature selection...")
            
            method = self.config['feature_selection']['method']
            k = self.config['feature_selection']['k']
            
            if method == 'selectkbest':
                self.feature_selector = SelectKBest(f_regression, k=k)
                X_train_scaled = self.feature_selector.fit_transform(X_train_scaled, self.y_train)
                X_test_scaled = self.feature_selector.transform(X_test_scaled)
                
                # Update feature names
                selected_indices = self.feature_selector.get_support(indices=True)
                self.feature_names = [self.feature_names[i] for i in selected_indices]
                
                logger.info(f"Selected {len(self.feature_names)} features")
        
        # Dimensionality reduction
        if self.config['dimensionality_reduction']['enabled']:
            logger.info("Applying dimensionality reduction...")
            
            method = self.config['dimensionality_reduction']['method']
            n_components = self.config['dimensionality_reduction']['n_components']
            
            if method == 'pca':
                self.pca = PCA(n_components=n_components, random_state=self.config['random_state'])
                X_train_scaled = self.pca.fit_transform(X_train_scaled)
                X_test_scaled = self.pca.transform(X_test_scaled)
                
                logger.info(f"Reduced to {X_train_scaled.shape[1]} PCA components")
                logger.info(f"Explained variance ratio: {self.pca.explained_variance_ratio_.sum():.3f}")
        
        return X_train_scaled, X_test_scaled
    
    def train_single_model(self, model_name: str, model: Any, X_train: np.ndarray, 
                          y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train a single model and evaluate performance"""
        logger.info(f"Training {model_name}...")
        
        start_time = datetime.now()
        
        try:
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            
            # Calculate metrics
            train_metrics = self._calculate_regression_metrics(y_train, y_train_pred)
            test_metrics = self._calculate_regression_metrics(y_test, y_test_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=self.config['cv_folds'],
                scoring=self.config['scoring_metric'],
                n_jobs=-1
            )
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            results = {
                'model': model,
                'model_name': model_name,
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'cv_scores': cv_scores,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'training_time': training_time,
                'predictions': {
                    'train': y_train_pred,
                    'test': y_test_pred
                }
            }
            
            # Store trained model
            self.trained_models[model_name] = model
            self.model_scores[model_name] = test_metrics['mse']
            
            logger.info(f"{model_name} - Test MSE: {test_metrics['mse']:.4f}, "
                       f"R²: {test_metrics['r2']:.4f}, Time: {training_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training {model_name}: {e}")
            return {
                'model_name': model_name,
                'error': str(e),
                'training_time': 0
            }
    
    def _calculate_regression_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics"""
        return {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
    
    def tune_hyperparameters(self, model_name: str, model: Any, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Perform hyperparameter tuning for a model"""
        logger.info(f"Tuning hyperparameters for {model_name}...")
        
        param_grids = self._get_param_grids()
        
        if model_name not in param_grids:
            logger.warning(f"No parameter grid defined for {model_name}")
            return model
        
        param_grid = param_grids[model_name]
        tuning_method = self.config['hyperparameter_tuning']['method']
        cv_folds = self.config['hyperparameter_tuning']['cv_folds']
        
        try:
            if tuning_method == 'grid':
                search = GridSearchCV(
                    model, param_grid,
                    cv=cv_folds,
                    scoring=self.config['scoring_metric'],
                    n_jobs=-1,
                    verbose=0
                )
            else:  # randomized
                n_iter = self.config['hyperparameter_tuning']['n_iter']
                search = RandomizedSearchCV(
                    model, param_grid,
                    n_iter=n_iter,
                    cv=cv_folds,
                    scoring=self.config['scoring_metric'],
                    random_state=self.config['random_state'],
                    n_jobs=-1,
                    verbose=0
                )
            
            search.fit(X_train, y_train)
            
            logger.info(f"{model_name} - Best score: {search.best_score_:.4f}")
            logger.info(f"{model_name} - Best params: {search.best_params_}")
            
            return search.best_estimator_
            
        except Exception as e:
            logger.error(f"Error tuning {model_name}: {e}")
            return model
    
    def _get_param_grids(self) -> Dict[str, Dict[str, List]]:
        """Get parameter grids for hyperparameter tuning"""
        return {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            },
            'knn': {
                'n_neighbors': [3, 5, 7, 9, 11],
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan', 'minkowski']
            },
            'ridge': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            },
            'lasso': {
                'alpha': [0.01, 0.1, 1.0, 10.0]
            },
            'elastic_net': {
                'alpha': [0.01, 0.1, 1.0, 10.0],
                'l1_ratio': [0.1, 0.5, 0.7, 0.9]
            },
            'svr': {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1],
                'epsilon': [0.01, 0.1, 0.2]
            },
            'mlp': {
                'hidden_layer_sizes': [(50,), (100,), (100, 50), (200, 100)],
                'learning_rate_init': [0.001, 0.01, 0.1],
                'alpha': [0.0001, 0.001, 0.01]
            }
        }
    
    def create_ensemble(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Create ensemble model from trained models"""
        if not self.config['ensemble_methods']['enabled']:
            return None
        
        logger.info("Creating ensemble model...")
        
        # Select top performing models
        top_models = []
        sorted_models = sorted(self.model_scores.items(), key=lambda x: x[1])[:3]
        
        for model_name, score in sorted_models:
            if model_name in self.trained_models:
                top_models.append((model_name, self.trained_models[model_name]))
        
        if len(top_models) < 2:
            logger.warning("Not enough models for ensemble")
            return None
        
        try:
            # Create voting regressor
            ensemble = VotingRegressor(
                estimators=top_models,
                n_jobs=-1
            )
            
            ensemble.fit(X_train, y_train)
            
            logger.info(f"Created ensemble with {len(top_models)} models: "
                       f"{[name for name, _ in top_models]}")
            
            return ensemble
            
        except Exception as e:
            logger.error(f"Error creating ensemble: {e}")
            return None
    
    def train_all_models(self, df: pd.DataFrame, target_column: str = None) -> Dict[str, Any]:
        """Train all models and return results"""
        logger.info("Starting comprehensive model training...")
        
        # Initialize models
        self.initialize_models()
        
        # Prepare data
        X, y, feature_names = self.prepare_data(df, target_column)
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # Preprocess features
        X_train_processed, X_test_processed = self.preprocess_features(X_train, X_test)
        
        # Train each model
        all_results = {}
        
        for model_name, model in self.models.items():
            # Hyperparameter tuning if enabled
            if self.config['hyperparameter_tuning']['enabled']:
                model = self.tune_hyperparameters(model_name, model, X_train_processed, y_train)
            
            # Train and evaluate
            results = self.train_single_model(
                model_name, model, X_train_processed, y_train, X_test_processed, y_test
            )
            
            all_results[model_name] = results
        
        # Create ensemble model
        ensemble = self.create_ensemble(X_train_processed, y_train)
        if ensemble:
            ensemble_results = self.train_single_model(
                'ensemble', ensemble, X_train_processed, y_train, X_test_processed, y_test
            )
            all_results['ensemble'] = ensemble_results
        
        # Select best model
        self._select_best_model()
        
        # Store results
        self.training_results = all_results
        
        logger.info("Model training completed!")
        logger.info(f"Best model: {self.best_model_name}")
        
        return all_results
    
    def _select_best_model(self):
        """Select the best performing model"""
        if not self.model_scores:
            return
        
        # Select model with lowest MSE
        best_model_name = min(self.model_scores.items(), key=lambda x: x[1])[0]
        self.best_model_name = best_model_name
        self.best_model = self.trained_models[best_model_name]
        
        logger.info(f"Selected best model: {best_model_name} "
                   f"(MSE: {self.model_scores[best_model_name]:.4f})")
    
    def evaluate_models(self) -> pd.DataFrame:
        """Create comprehensive model evaluation report"""
        if not self.training_results:
            logger.warning("No training results available")
            return pd.DataFrame()
        
        evaluation_data = []
        
        for model_name, results in self.training_results.items():
            if 'error' in results:
                continue
                
            row = {
                'Model': model_name,
                'Train_MSE': results['train_metrics']['mse'],
                'Test_MSE': results['test_metrics']['mse'],
                'Train_R2': results['train_metrics']['r2'],
                'Test_R2': results['test_metrics']['r2'],
                'Train_MAE': results['train_metrics']['mae'],
                'Test_MAE': results['test_metrics']['mae'],
                'CV_Mean': results['cv_mean'],
                'CV_Std': results['cv_std'],
                'Training_Time': results['training_time'],
                'Overfitting': results['train_metrics']['mse'] - results['test_metrics']['mse']
            }
            evaluation_data.append(row)
        
        df_eval = pd.DataFrame(evaluation_data)
        
        if not df_eval.empty:
            # Sort by test performance
            df_eval = df_eval.sort_values('Test_MSE')
            
            # Add ranking
            df_eval['Rank'] = range(1, len(df_eval) + 1)
        
        return df_eval
    
    def get_feature_importance(self, model_name: str = None) -> Dict[str, float]:
        """Get feature importance from trained model"""
        model_name = model_name or self.best_model_name
        
        if model_name not in self.trained_models:
            logger.warning(f"Model {model_name} not found")
            return {}
        
        model = self.trained_models[model_name]
        
        try:
            # Tree-based models
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            # Linear models
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_)
            else:
                logger.warning(f"Feature importance not available for {model_name}")
                return {}
            
            # Create importance dictionary
            feature_importance = {}
            for i, importance in enumerate(importances):
                if i < len(self.feature_names):
                    feature_importance[self.feature_names[i]] = float(importance)
            
            # Sort by importance
            feature_importance = dict(sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            ))
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def predict(self, X: np.ndarray, model_name: str = None) -> np.ndarray:
        """Make predictions using trained model"""
        model_name = model_name or self.best_model_name
        
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.trained_models[model_name]
        
        # Apply same preprocessing as training
        X_processed = self.scaler.transform(X)
        
        if self.feature_selector:
            X_processed = self.feature_selector.transform(X_processed)
        
        if self.pca:
            X_processed = self.pca.transform(X_processed)
        
        return model.predict(X_processed)
    
    def save_models(self, model_dir: str = None):
        """Save all trained models and preprocessors"""
        model_dir = Path(model_dir or self.config['model_dir'])
        model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving models to {model_dir}...")
        
        # Save trained models
        for model_name, model in self.trained_models.items():
            model_path = model_dir / f"{model_name}_model.pkl"
            joblib.dump(model, model_path)
        
        # Save preprocessors
        joblib.dump(self.scaler, model_dir / "scaler.pkl")
        
        if self.feature_selector:
            joblib.dump(self.feature_selector, model_dir / "feature_selector.pkl")
        
        if self.pca:
            joblib.dump(self.pca, model_dir / "pca.pkl")
        
        # Save metadata
        metadata = {
            'feature_names': self.feature_names,
            'best_model': self.best_model_name,
            'model_scores': self.model_scores,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved {len(self.trained_models)} models and preprocessors")
    
    def load_models(self, model_dir: str):
        """Load trained models and preprocessors"""
        model_dir = Path(model_dir)
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {model_dir}")
        
        logger.info(f"Loading models from {model_dir}...")
        
        # Load metadata
        metadata_path = model_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata.get('feature_names', [])
            self.best_model_name = metadata.get('best_model')
            self.model_scores = metadata.get('model_scores', {})
        
        # Load preprocessors
        scaler_path = model_dir / "scaler.pkl"
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
        
        feature_selector_path = model_dir / "feature_selector.pkl"
        if feature_selector_path.exists():
            self.feature_selector = joblib.load(feature_selector_path)
        
        pca_path = model_dir / "pca.pkl"
        if pca_path.exists():
            self.pca = joblib.load(pca_path)
        
        # Load models
        self.trained_models = {}
        for model_file in model_dir.glob("*_model.pkl"):
            model_name = model_file.stem.replace('_model', '')
            self.trained_models[model_name] = joblib.load(model_file)
        
        # Set best model
        if self.best_model_name and self.best_model_name in self.trained_models:
            self.best_model = self.trained_models[self.best_model_name]
        
        logger.info(f"Loaded {len(self.trained_models)} models")
    
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate comprehensive training report"""
        if not self.training_results:
            return {}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'data_info': {
                'n_samples': len(self.y_train) + len(self.y_test) if self.y_train is not None else 0,
                'n_features': len(self.feature_names),
                'train_samples': len(self.y_train) if self.y_train is not None else 0,
                'test_samples': len(self.y_test) if self.y_test is not None else 0
            },
            'model_performance': {},
            'best_model': {
                'name': self.best_model_name,
                'score': self.model_scores.get(self.best_model_name, 0) if self.best_model_name else 0
            },
            'feature_importance': self.get_feature_importance()
        }
        
        # Add performance for each model
        for model_name, results in self.training_results.items():
            if 'error' not in results:
                report['model_performance'][model_name] = {
                    'test_mse': results['test_metrics']['mse'],
                    'test_r2': results['test_metrics']['r2'],
                    'cv_mean': results['cv_mean'],
                    'cv_std': results['cv_std'],
                    'training_time': results['training_time']
                }
        
        return report


def train_movie_recommendation_models(data_path: str, config: Dict[str, Any] = None) -> MovieRecommendationTrainer:
    """
    Convenience function to train movie recommendation models
    
    Args:
        data_path: Path to preprocessed data file
        config: Training configuration
        
    Returns:
        Trained MovieRecommendationTrainer instance
    """
    # Load data
    if data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    elif data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.json'):
        df = pd.read_json(data_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Initialize trainer
    trainer = MovieRecommendationTrainer(config)
    
    # Train all models
    results = trainer.train_all_models(df)
    
    # Save models if enabled
    if trainer.config['save_models']:
        trainer.save_models()
    
    return trainer


class ModelEvaluator:
    """
    Model evaluation and comparison utilities
    """
    
    def __init__(self, trainer: MovieRecommendationTrainer):
        self.trainer = trainer
        self.evaluation_results = {}
    
    def cross_validate_models(self, X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> Dict[str, Dict[str, float]]:
        """Perform cross-validation on all trained models"""
        logger.info(f"Performing {cv_folds}-fold cross-validation...")
        
        results = {}
        
        for model_name, model in self.trainer.trained_models.items():
            try:
                # Cross-validation scores
                cv_scores = cross_val_score(
                    model, X, y, 
                    cv=cv_folds, 
                    scoring='neg_mean_squared_error',
                    n_jobs=-1
                )
                
                r2_scores = cross_val_score(
                    model, X, y,
                    cv=cv_folds,
                    scoring='r2',
                    n_jobs=-1
                )
                
                results[model_name] = {
                    'mse_mean': -cv_scores.mean(),
                    'mse_std': cv_scores.std(),
                    'r2_mean': r2_scores.mean(),
                    'r2_std': r2_scores.std(),
                    'cv_scores': cv_scores.tolist()
                }
                
                logger.info(f"{model_name} - CV MSE: {-cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
                
            except Exception as e:
                logger.error(f"Error in cross-validation for {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        self.evaluation_results['cross_validation'] = results
        return results
    
    def learning_curves(self, X: np.ndarray, y: np.ndarray, model_name: str = None) -> Dict[str, Any]:
        """Generate learning curves for model analysis"""
        from sklearn.model_selection import learning_curve
        
        model_name = model_name or self.trainer.best_model_name
        if model_name not in self.trainer.trained_models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.trainer.trained_models[model_name]
        
        logger.info(f"Generating learning curves for {model_name}...")
        
        try:
            train_sizes, train_scores, val_scores = learning_curve(
                model, X, y,
                cv=5,
                n_jobs=-1,
                train_sizes=np.linspace(0.1, 1.0, 10),
                scoring='neg_mean_squared_error'
            )
            
            results = {
                'train_sizes': train_sizes.tolist(),
                'train_scores_mean': (-train_scores.mean(axis=1)).tolist(),
                'train_scores_std': train_scores.std(axis=1).tolist(),
                'val_scores_mean': (-val_scores.mean(axis=1)).tolist(),
                'val_scores_std': val_scores.std(axis=1).tolist()
            }
            
            self.evaluation_results['learning_curves'] = {model_name: results}
            return results
            
        except Exception as e:
            logger.error(f"Error generating learning curves: {e}")
            return {}
    
    def residual_analysis(self, model_name: str = None) -> Dict[str, Any]:
        """Perform residual analysis on model predictions"""
        model_name = model_name or self.trainer.best_model_name
        
        if (model_name not in self.trainer.training_results or 
            'predictions' not in self.trainer.training_results[model_name]):
            logger.warning(f"No predictions available for {model_name}")
            return {}
        
        results = self.trainer.training_results[model_name]
        
        # Calculate residuals
        train_residuals = self.trainer.y_train - results['predictions']['train']
        test_residuals = self.trainer.y_test - results['predictions']['test']
        
        analysis = {
            'train_residuals': {
                'mean': float(train_residuals.mean()),
                'std': float(train_residuals.std()),
                'min': float(train_residuals.min()),
                'max': float(train_residuals.max()),
                'skewness': float(pd.Series(train_residuals).skew()),
                'kurtosis': float(pd.Series(train_residuals).kurtosis())
            },
            'test_residuals': {
                'mean': float(test_residuals.mean()),
                'std': float(test_residuals.std()),
                'min': float(test_residuals.min()),
                'max': float(test_residuals.max()),
                'skewness': float(pd.Series(test_residuals).skew()),
                'kurtosis': float(pd.Series(test_residuals).kurtosis())
            }
        }
        
        self.evaluation_results['residual_analysis'] = {model_name: analysis}
        return analysis
    
    def model_interpretability(self, model_name: str = None, top_features: int = 20) -> Dict[str, Any]:
        """Analyze model interpretability and feature importance"""
        model_name = model_name or self.trainer.best_model_name
        
        if model_name not in self.trainer.trained_models:
            logger.warning(f"Model {model_name} not found")
            return {}
        
        model = self.trainer.trained_models[model_name]
        
        interpretation = {
            'model_type': type(model).__name__,
            'feature_importance': self.trainer.get_feature_importance(model_name),
            'model_parameters': {},
            'complexity_metrics': {}
        }
        
        # Get model parameters
        try:
            interpretation['model_parameters'] = model.get_params()
        except:
            pass
        
        # Calculate complexity metrics
        try:
            if hasattr(model, 'n_estimators'):
                interpretation['complexity_metrics']['n_estimators'] = model.n_estimators
            if hasattr(model, 'max_depth'):
                interpretation['complexity_metrics']['max_depth'] = model.max_depth
            if hasattr(model, 'n_features_in_'):
                interpretation['complexity_metrics']['n_features'] = model.n_features_in_
        except:
            pass
        
        # Top important features
        feature_importance = interpretation['feature_importance']
        if feature_importance:
            top_features_dict = dict(list(feature_importance.items())[:top_features])
            interpretation['top_features'] = top_features_dict
        
        self.evaluation_results['interpretability'] = {model_name: interpretation}
        return interpretation
    
    def compare_models(self) -> pd.DataFrame:
        """Create detailed model comparison"""
        if not self.trainer.training_results:
            return pd.DataFrame()
        
        comparison_data = []
        
        for model_name, results in self.trainer.training_results.items():
            if 'error' in results:
                continue
            
            # Basic metrics
            row = {
                'Model': model_name,
                'Test_MSE': results['test_metrics']['mse'],
                'Test_RMSE': results['test_metrics']['rmse'],
                'Test_MAE': results['test_metrics']['mae'],
                'Test_R2': results['test_metrics']['r2'],
                'CV_Mean': results['cv_mean'],
                'CV_Std': results['cv_std'],
                'Training_Time': results['training_time']
            }
            
            # Add complexity metrics
            model = self.trainer.trained_models[model_name]
            row['Model_Type'] = type(model).__name__
            
            if hasattr(model, 'n_estimators'):
                row['N_Estimators'] = model.n_estimators
            if hasattr(model, 'max_depth'):
                row['Max_Depth'] = model.max_depth
            
            # Overfitting measure
            row['Overfitting'] = results['train_metrics']['mse'] - results['test_metrics']['mse']
            
            # Efficiency score (performance vs time)
            row['Efficiency'] = results['test_metrics']['r2'] / max(results['training_time'], 0.1)
            
            comparison_data.append(row)
        
        df_comparison = pd.DataFrame(comparison_data)
        
        if not df_comparison.empty:
            # Add rankings
            df_comparison['MSE_Rank'] = df_comparison['Test_MSE'].rank()
            df_comparison['R2_Rank'] = df_comparison['Test_R2'].rank(ascending=False)
            df_comparison['Time_Rank'] = df_comparison['Training_Time'].rank()
            df_comparison['Overall_Rank'] = (
                df_comparison['MSE_Rank'] + df_comparison['R2_Rank'] + df_comparison['Time_Rank']
            ).rank()
            
            # Sort by overall performance
            df_comparison = df_comparison.sort_values('Overall_Rank')
        
        return df_comparison
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_models': len(self.trainer.trained_models),
                'best_model': self.trainer.best_model_name,
                'best_score': self.trainer.model_scores.get(self.trainer.best_model_name, 0)
            },
            'model_comparison': self.compare_models().to_dict('records'),
            'evaluation_results': self.evaluation_results
        }
        
        return report


class RecommendationEngine:
    """
    Production-ready recommendation engine using trained models
    """
    
    def __init__(self, model_dir: str = None, trainer: MovieRecommendationTrainer = None):
        if trainer:
            self.trainer = trainer
        else:
            self.trainer = MovieRecommendationTrainer()
            if model_dir:
                self.trainer.load_models(model_dir)
        
        self.recommendation_cache = {}
        self.model_loaded = bool(self.trainer.best_model)
    
    def predict_rating(self, features: np.ndarray, model_name: str = None) -> np.ndarray:
        """Predict movie ratings for given features"""
        if not self.model_loaded:
            raise ValueError("No model loaded")
        
        return self.trainer.predict(features, model_name)
    
    def recommend_movies(self, user_preferences: Dict[str, Any], movie_features: pd.DataFrame,
                        n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Generate movie recommendations based on user preferences"""
        if not self.model_loaded:
            raise ValueError("No model loaded")
        
        try:
            # Extract features for prediction
            feature_cols = [col for col in movie_features.columns if col in self.trainer.feature_names]
            X = movie_features[feature_cols].fillna(0).values
            
            # Predict ratings
            predicted_ratings = self.predict_rating(X)
            
            # Create recommendations
            recommendations = []
            for i, (idx, movie) in enumerate(movie_features.iterrows()):
                recommendation = {
                    'movie_id': idx,
                    'title': movie.get('title', 'Unknown'),
                    'predicted_rating': float(predicted_ratings[i]),
                    'confidence_score': self._calculate_confidence(predicted_ratings[i]),
                    'genre': movie.get('genre', ''),
                    'year': movie.get('year', 0),
                    'description': movie.get('description', ''),
                    'match_score': self._calculate_match_score(movie, user_preferences)
                }
                recommendations.append(recommendation)
            
            # Sort by predicted rating and match score
            recommendations.sort(
                key=lambda x: (x['predicted_rating'] * 0.7 + x['match_score'] * 0.3),
                reverse=True
            )
            
            return recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_confidence(self, predicted_rating: float) -> float:
        """Calculate confidence score for prediction"""
        # Simple confidence based on rating range
        # Higher ratings and mid-range ratings get higher confidence
        if 7.0 <= predicted_rating <= 9.0:
            return 0.9
        elif 6.0 <= predicted_rating < 7.0:
            return 0.7
        elif predicted_rating >= 9.0:
            return 0.8
        else:
            return 0.5
    
    def _calculate_match_score(self, movie: pd.Series, user_preferences: Dict[str, Any]) -> float:
        """Calculate how well movie matches user preferences"""
        match_score = 0.0
        
        # Genre matching
        if 'genres' in user_preferences and movie.get('genre'):
            user_genres = set(user_preferences['genres'])
            movie_genres = set(movie['genre'].split(', '))
            genre_overlap = len(user_genres.intersection(movie_genres))
            match_score += (genre_overlap / len(user_genres)) * 0.4
        
        # Year preference
        if 'decade' in user_preferences and movie.get('year'):
            preferred_decade = user_preferences['decade']
            movie_decade = (movie['year'] // 10) * 10
            
            decade_ranges = {
                '2020s': (2020, 2029),
                '2010s': (2010, 2019),
                '2000s': (2000, 2009),
                '1990s': (1990, 1999),
                '1980s': (1980, 1989),
                '1970s': (1970, 1979),
                'Classic (Before 1970)': (1900, 1969)
            }
            
            if preferred_decade in decade_ranges:
                start, end = decade_ranges[preferred_decade]
                if start <= movie['year'] <= end:
                    match_score += 0.2
        
        # Additional matching logic can be added here
        
        return min(match_score, 1.0)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model"""
        if not self.model_loaded:
            return {'status': 'No model loaded'}
        
        return {
            'status': 'Model loaded',
            'best_model': self.trainer.best_model_name,
            'available_models': list(self.trainer.trained_models.keys()),
            'feature_count': len(self.trainer.feature_names),
            'model_score': self.trainer.model_scores.get(self.trainer.best_model_name, 0)
        }


if __name__ == "__main__":
    """Example usage and testing"""
    
    # Example configuration
    config = {
        'target_column': 'rating',
        'test_size': 0.2,
        'cv_folds': 5,
        'feature_selection': {'enabled': True, 'k': 30},
        'hyperparameter_tuning': {'enabled': True, 'method': 'randomized', 'n_iter': 20},
        'ensemble_methods': {'enabled': True},
        'model_types': ['random_forest', 'gradient_boosting', 'knn', 'ridge'],
        'save_models': True
    }
    
    try:
        # Load preprocessed data (you'll need to adjust the path)
        data_path = "preprocessed_movies.parquet"  # or .csv or .json
        
        # Train models
        trainer = train_movie_recommendation_models(data_path, config)
        
        # Evaluate models
        evaluator = ModelEvaluator(trainer)
        
        # Get model comparison
        comparison_df = evaluator.compare_models()
        print("\nModel Comparison:")
        print(comparison_df)
        
        # Get feature importance
        feature_importance = trainer.get_feature_importance()
        print(f"\nTop 10 Important Features:")
        for feature, importance in list(feature_importance.items())[:10]:
            print(f"{feature}: {importance:.4f}")
        
        # Generate reports
        training_report = trainer.generate_training_report()
        evaluation_report = evaluator.generate_evaluation_report()
        
        print(f"\nTraining completed successfully!")
        print(f"Best model: {trainer.best_model_name}")
        print(f"Best score: {trainer.model_scores[trainer.best_model_name]:.4f}")
        
        # Test recommendation engine
        engine = RecommendationEngine(trainer=trainer)
        model_info = engine.get_model_info()
        print(f"\nRecommendation Engine Status: {model_info['status']}")
        
    except Exception as e:
        print(f"Error in model training: {e}")
        logger.error(f"Training failed: {e}")