import logging
from src.simulation import simulate_backtest

def main() -> None:
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s [%(levelname)s] %(message)s')
    try:
        simulate_backtest()
    except Exception as e:
        logging.exception("An error occurred during simulation: %s", e)

if __name__ == '__main__':
    main()
