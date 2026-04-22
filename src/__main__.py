try:
    from .cli import main
except ImportError:
    from src.cli import main


if __name__ == "__main__":
    main()
