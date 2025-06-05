import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the bot."""

    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.__initialized = False  # Add this line
        return cls._instance

    def __init__(self):
        if self.__initialized:  # Check if already initialized
            return
        self.__initialized = True  # Set initialized flag
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME')
        self.OWNER_ID = int(os.getenv('OWNER_ID', '1631827811'))
        self.ADMINS = [int(x) for x in os.getenv('ADMINS', str(self.OWNER_ID)).split(',')]
        self.FORCED_CHANNEL_ID = int(os.getenv('FORCED_CHANNEL_ID', '-1001234567890'))
        self.FORCED_CHANNEL_USERNAME = os.getenv('FORCED_CHANNEL_USERNAME', 'example_channel')
        self.RECHARGE_GROUP_ID = int(os.getenv('RECHARGE_GROUP_ID', '-1001234567890'))
        self.PURCHASE_GROUP_ID = int(os.getenv('PURCHASE_GROUP_ID', '-1001234567890'))
        self.USD_RATE = os.getenv('USD_RATE', '10000')
        self.USDT_RATE = os.getenv('USDT_RATE', '10000')
        self.DB_PATH = "diamond_store.db"  # Define DB_PATH here
        self.SYRIATEL_CASH_NUMBERS = [num.strip() for num in os.getenv('SYRIATEL_CASH_NUMBERS', '').split(',')]
        self.USDT_WALLET_COINEX = os.getenv('USDT_WALLET_COINEX')
        self.USDT_WALLET_CWALLET = os.getenv('USDT_WALLET_CWALLET')
        self.USD_WALLET_PAYEER = os.getenv('USD_WALLET_PAYEER')
        self.USDT_WALLET_PEB20 = os.getenv('USDT_WALLET_PEB20')
        self.BOT_USERNAME = os.getenv('BOT_USERNAME', 'diamond_store_sy_bot')

    def update_usd_rate(self, new_rate: str) -> bool:
        """Update the USD rate in the .env file."""
        return self._update_env_variable('USD_RATE', new_rate)

    def update_usdt_rate(self, new_rate: str) -> bool:
        """Update the USDT rate in the .env file."""
        return self._update_env_variable('USDT_RATE', new_rate)

    def update_syriatel_numbers(self, numbers: list[str]) -> bool:
        """Update the Syriatel Cash numbers in the .env file."""
        numbers_str = ','.join(numbers)
        return self._update_env_variable('SYRIATEL_CASH_NUMBERS', numbers_str)

    def update_usdt_wallets(self, wallets: dict) -> bool:
        """Update the USDT wallets in the .env file."""
        success = True
        success &= self._update_env_variable('USDT_WALLET_COINEX', wallets.get('coinex', ''))
        success &= self._update_env_variable('USDT_WALLET_CWALLET', wallets.get('cwallet', ''))
        success &= self._update_env_variable('USD_WALLET_PAYEER', wallets.get('payeer', ''))
        success &= self._update_env_variable('USDT_WALLET_PEB20', wallets.get('peb20', ''))
        return success

    def _update_env_variable(self, variable_name: str, new_value: str) -> bool:
        """Helper function to update a variable in the .env file."""
        try:
            dotenv_path = '.env'
            with open(dotenv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            updated = False
            with open(dotenv_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.startswith(f"{variable_name}="):
                        f.write(f"{variable_name}={new_value}\n")
                        updated = True
                    else:
                        f.write(line)

                if not updated:
                    f.write(f"{variable_name}={new_value}\n")

            os.environ[variable_name] = new_value  # Update the environment variable

            # Update the Config object's attribute
            if variable_name == 'USD_RATE':
                self.USD_RATE = new_value
            elif variable_name == 'USDT_RATE':
                self.USDT_RATE = new_value
            elif variable_name == 'SYRIATEL_CASH_NUMBERS':
                self.SYRIATEL_CASH_NUMBERS = [num.strip() for num in new_value.split(',')]
            elif variable_name == 'USDT_WALLET_COINEX':
                self.USDT_WALLET_COINEX = new_value
            elif variable_name == 'USDT_WALLET_CWALLET':
                self.USDT_WALLET_CWALLET = new_value
            elif variable_name == 'USD_WALLET_PAYEER':
                self.USD_WALLET_PAYEER = new_value
            elif variable_name == 'USD_WALLET_PEB20':
                self.USDT_WALLET_PEB20 = new_value

            return True
        except Exception as e:
            print(f"Error updating {variable_name} in .env: {e}")
            return False


_config = Config()  # Create a single instance

def get_config():
    """Function to access the Config instance."""
    return _config


