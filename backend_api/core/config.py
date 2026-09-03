"""Application configuration and environment settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Faculty Workload Allocation System"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./faculty_workload.db"
    # For production, use PostgreSQL:
    # DATABASE_URL: str = "postgresql://user:password@localhost/faculty_workload"
    
    # Optimization Engine
    GA_POPULATION_SIZE: int = 50
    GA_GENERATIONS: int = 100
    GA_MUTATION_RATE: float = 0.15
    GA_CROSSOVER_RATE: float = 0.85
    TABU_TENURE: int = 10
    TABU_MAX_ITERATIONS: int = 200
    
    # Constraints
    DEFAULT_FT_MAX: int = 21  # Full-time max units
    DEFAULT_PT_MAX: int = 12  # Part-time max units
    DEFAULT_OVERLOAD_LIMIT: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
